import assert from "node:assert/strict";
import http from "node:http";
import type { AddressInfo } from "node:net";
import { after, test } from "node:test";

import { ask, DEFAULT_EFFORT, DEFAULT_MODEL, HubError } from "./hub.ts";
import type { HubOptions, Question } from "./hub.ts";

// A Hub that answers what each test tells it to. No test here reaches the real one.
interface Seen {
  method: string;
  url: string;
  headers: http.IncomingHttpHeaders;
  body: Record<string, unknown>;
}

type Respond = (response: http.ServerResponse, request: http.IncomingMessage, attempt: number) => void;

const seen: Seen[] = [];
let respond: Respond = () => {};

const server = http.createServer((request, response) => {
  const chunks: Buffer[] = [];
  request.on("data", (chunk: Buffer) => chunks.push(chunk));
  request.on("end", () => {
    seen.push({
      method: request.method ?? "",
      url: request.url ?? "",
      headers: request.headers,
      body: JSON.parse(Buffer.concat(chunks).toString("utf8")) as Record<string, unknown>,
    });
    respond(response, request, seen.length);
  });
});
await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
const baseUrl = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
after(() => {
  server.closeAllConnections();
  server.close();
});

const json = (response: http.ServerResponse, status: number, value: unknown, headers: Record<string, string> = {}) => {
  response.writeHead(status, { "content-type": "application/json", ...headers });
  response.end(JSON.stringify(value));
};

const completion = (content: string, extra: Record<string, unknown> = {}) => ({
  id: "chatcmpl-1",
  model: "gpt-5.6-sol",
  choices: [{ index: 0, finish_reason: "stop", message: { role: "assistant", content } }],
  usage: { prompt_tokens: 1200, completion_tokens: 340, total_tokens: 1540, cost_usd: 0.0123 },
  ...extra,
});

const QUESTION: Question = {
  model: DEFAULT_MODEL,
  effort: DEFAULT_EFFORT,
  maxTokens: 64_000,
  messages: [
    { role: "system", content: "The guidance." },
    { role: "user", content: "The document." },
  ],
  schema: { name: "translation", schema: { type: "object", properties: { title: { type: "string" } } } },
};

const retried: string[] = [];
const quick: HubOptions = { baseUrl, backoffMs: () => 1, onRetry: (reason) => retried.push(reason) };

function hub(next: Respond): void {
  seen.length = 0;
  retried.length = 0;
  respond = next;
}

const failure = async (options: HubOptions = quick): Promise<HubError> => {
  try {
    await ask(QUESTION, options);
  } catch (error) {
    assert.ok(error instanceof HubError, `expected a HubError, got ${String(error)}`);
    return error;
  }
  throw new Error("the call did not fail");
};

test("the question is one POST to /v1/chat/completions, in the Chat Completions shape", async () => {
  hub((response) => json(response, 200, completion('{"title":"Sobre"}')));
  const answer = await ask(QUESTION, quick);
  assert.equal(seen.length, 1);
  const [request] = seen;
  assert.equal(request!.method, "POST");
  assert.equal(request!.url, "/v1/chat/completions");
  assert.equal(request!.headers["content-type"], "application/json");
  assert.equal(request!.headers.authorization, undefined, "the Hub knows the caller by its connection");
  assert.deepEqual(request!.body, {
    model: "gpt-5.6-sol",
    messages: [
      { role: "system", content: "The guidance." },
      { role: "user", content: "The document." },
    ],
    reasoning_effort: "high",
    max_tokens: 64_000,
    response_format: {
      type: "json_schema",
      json_schema: { name: "translation", schema: { type: "object", properties: { title: { type: "string" } } } },
    },
  });
  assert.deepEqual(answer, {
    content: '{"title":"Sobre"}',
    model: "gpt-5.6-sol",
    usage: { prompt_tokens: 1200, completion_tokens: 340, total_tokens: 1540, cost_usd: 0.0123 },
  });
});

test("MARE_HUB names another Hub", async () => {
  hub((response) => json(response, 200, completion("{}")));
  const before = process.env.MARE_HUB;
  process.env.MARE_HUB = `${baseUrl}/`;
  try {
    await ask(QUESTION);
  } finally {
    if (before === undefined) delete process.env.MARE_HUB;
    else process.env.MARE_HUB = before;
  }
  assert.equal(seen.length, 1);
  assert.equal(seen[0]!.url, "/v1/chat/completions");
});

test("an error the Hub reports is raised with its message, and not sent again", async () => {
  for (const status of [400, 401, 404, 422, 500, 502]) {
    hub((response) => json(response, status, { error: { message: `unknown model 'gpt-9' (${status})`, type: "invalid_request_error" } }));
    const error = await failure();
    assert.equal(error.status, status);
    assert.equal(error.message, `The Hub answered ${status}: unknown model 'gpt-9' (${status})`);
    assert.equal(seen.length, 1, `${status} is not retried`);
    assert.deepEqual(retried, []);
  }
});

test("an error that is not the Hub's JSON is shown as it came", async () => {
  hub((response) => {
    response.writeHead(502, { "content-type": "text/html" });
    response.end("<html>Bad Gateway</html>");
  });
  assert.equal((await failure()).message, "The Hub answered 502: <html>Bad Gateway</html>");
});

test("429 and 503 are sent again, after a wait", async () => {
  for (const status of [429, 503]) {
    hub((response, _request, attempt) =>
      attempt < 3
        ? json(response, status, { error: { message: "busy" } }, { "retry-after": "0" })
        : json(response, 200, completion('{"ok":true}')),
    );
    const answer = await ask(QUESTION, quick);
    assert.equal(answer.content, '{"ok":true}');
    assert.equal(seen.length, 3);
    assert.deepEqual(retried, [`The Hub answered ${status}: busy`, `The Hub answered ${status}: busy`]);
    assert.deepEqual(seen[2]!.body, seen[0]!.body, "the same question each time");
  }
});

test("a connection that drops is tried again", async () => {
  hub((response, request, attempt) => (attempt === 1 ? request.socket.destroy() : json(response, 200, completion("{}"))));
  const answer = await ask(QUESTION, quick);
  assert.equal(answer.content, "{}");
  assert.equal(seen.length, 2);
  assert.match(retried[0]!, /^Could not reach the Hub at http:\/\/127\.0\.0\.1:\d+: /);
});

test("an answer cut off on its way is tried again", async () => {
  hub((response, request, attempt) => {
    if (attempt > 1) return json(response, 200, completion("{}"));
    response.writeHead(200, { "content-type": "application/json", "content-length": "500" });
    response.write('{"choices":[');
    setTimeout(() => request.socket.destroy(), 5);
  });
  await ask(QUESTION, quick);
  assert.equal(seen.length, 2);
});

test("it gives up after a few tries", async () => {
  hub((response) => json(response, 503, { error: { message: "still busy" } }));
  const error = await failure({ ...quick, retries: 2 });
  assert.equal(error.status, 503);
  assert.equal(seen.length, 3, "one try and two retries");
  assert.equal(retried.length, 2);
});

test("a Hub that is not there is an error that says where it was looked for", async () => {
  const closed = http.createServer();
  await new Promise<void>((resolve) => closed.listen(0, "127.0.0.1", resolve));
  const { port } = closed.address() as AddressInfo;
  await new Promise((resolve) => closed.close(resolve));
  retried.length = 0;
  const error = await failure({ ...quick, baseUrl: `http://127.0.0.1:${port}`, retries: 1 });
  assert.equal(error.status, null);
  assert.match(error.message, new RegExp(`^Could not reach the Hub at http://127\\.0\\.0\\.1:${port}: `));
  assert.equal(retried.length, 1);
});

test("an answer that takes too long is an error, and is not asked for again", async () => {
  hub(() => {
    // never answers
  });
  const error = await failure({ ...quick, timeoutMs: 40 });
  assert.equal(error.message, "The Hub did not answer within 0 seconds");
  assert.equal(seen.length, 1);
  assert.deepEqual(retried, []);
});

test("an answer cut off at max_tokens is an error, not a translation", async () => {
  hub((response) => json(response, 200, { ...completion('{"title":"So'), choices: [{ finish_reason: "length", message: { content: '{"title":"So' } }] }));
  assert.match((await failure()).message, /cut off at max_tokens/);
  assert.equal(seen.length, 1);
});

test("an answer without a message, or a refusal, is an error", async () => {
  hub((response) => json(response, 200, { choices: [] }));
  assert.match((await failure()).message, /has no message/);
  hub((response) => json(response, 200, { choices: [{ finish_reason: "stop", message: { content: null, refusal: "I can't help with that." } }] }));
  assert.equal((await failure()).message, "The model refused: I can't help with that.");
  hub((response) => {
    response.writeHead(200);
    response.end("not json");
  });
  assert.equal((await failure()).message, "The Hub's answer is not JSON: not json");
});

test("an answer without usage still comes back", async () => {
  hub((response) => json(response, 200, { choices: [{ finish_reason: "stop", message: { content: "{}" } }] }));
  assert.deepEqual(await ask(QUESTION, quick), { content: "{}", model: "", usage: {} });
});
