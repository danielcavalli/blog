// One question to a model, through the Maré Hub's gateway.
//
//   POST <hub>/v1/chat/completions      OpenAI Chat Completions, answered whole
//
// The Hub knows the caller by its tailnet connection, so there is no credential to send. It retries
// upstream failures itself: what is retried here is only what never reached it or what it asked to
// have sent again (a network error, 429, 503).
//
// The request goes through `node:http(s)`, not `fetch`: Node's `fetch` gives up on a response whose
// headers take more than five minutes, and a long post at high effort takes longer than that.

import http from "node:http";
import https from "node:https";

export const DEFAULT_HUB = "https://hub.tail73a546.ts.net";
export const DEFAULT_MODEL = "gpt-5.6-sol";
export const DEFAULT_EFFORT = "high";
/** Room for a long post and the thinking before it. Without it, Claude models stop at 8192. */
export const DEFAULT_MAX_TOKENS = 64_000;

export interface Message {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface Question {
  model: string;
  effort: string;
  maxTokens: number;
  messages: Message[];
  /** The structured output asked for. */
  schema: { name: string; schema: Record<string, unknown> };
}

export interface Usage {
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  cost_usd?: number;
  [key: string]: unknown;
}

export interface Answer {
  /** The model's message, which is the JSON asked for, as text. */
  content: string;
  /** The model that answered, as the Hub names it. */
  model: string;
  usage: Usage;
}

export interface HubOptions {
  /** The Hub's address. Default: `MARE_HUB`, or the Hub on the tailnet. */
  baseUrl?: string;
  /** How long one attempt may take. */
  timeoutMs?: number;
  /** How many times a failed attempt is sent again. */
  retries?: number;
  /** How long to wait before retry `n` (from 1). */
  backoffMs?: (attempt: number) => number;
  /** Told of each retry. */
  onRetry?: (reason: string, waitMs: number) => void;
}

export class HubError extends Error {
  /** The HTTP status, when the Hub answered. */
  status: number | null;
  constructor(message: string, status: number | null = null) {
    super(message);
    this.name = "HubError";
    this.status = status;
  }
}

interface Reply {
  status: number;
  retryAfter: string | undefined;
  body: string;
}

class Timeout extends Error {}

function post(url: URL, body: string, timeoutMs: number): Promise<Reply> {
  return new Promise((resolve, reject) => {
    let timedOut = false;
    const fail = (error: Error) => reject(timedOut ? new Timeout() : error);
    const request = (url.protocol === "https:" ? https : http).request(
      url,
      { method: "POST", headers: { "content-type": "application/json", "content-length": Buffer.byteLength(body) } },
      (response) => {
        const chunks: Buffer[] = [];
        response.on("data", (chunk: Buffer) => chunks.push(chunk));
        response.on("error", fail);
        response.on("close", () => {
          if (!response.complete) fail(new Error("the connection closed before the answer was complete"));
        });
        response.on("end", () => {
          const retryAfter = response.headers["retry-after"];
          resolve({
            status: response.statusCode ?? 0,
            retryAfter: Array.isArray(retryAfter) ? retryAfter[0] : retryAfter,
            body: Buffer.concat(chunks).toString("utf8"),
          });
        });
      },
    );
    // The answer comes whole at the end, so the connection is silent for minutes: keep it alive.
    request.on("socket", (socket) => socket.setKeepAlive(true, 30_000));
    const timer = setTimeout(() => {
      timedOut = true;
      request.destroy(new Timeout());
    }, timeoutMs);
    request.on("error", fail);
    request.on("close", () => clearTimeout(timer));
    request.end(body);
  });
}

// What the Hub says went wrong: `{"error":{"message":"…"}}`, or whatever it sent instead.
function errorMessage(body: string): string {
  try {
    const parsed = JSON.parse(body) as { error?: { message?: unknown } | string };
    if (typeof parsed.error === "string") return parsed.error;
    if (typeof parsed.error?.message === "string") return parsed.error.message;
  } catch {
    // not JSON: say what it was
  }
  return body.trim().slice(0, 300) || "(no message)";
}

const sleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

/** Ask the model, and return its answer whole. Throws `HubError` with what went wrong. */
export async function ask(question: Question, options: HubOptions = {}): Promise<Answer> {
  const base = (options.baseUrl ?? process.env.MARE_HUB ?? DEFAULT_HUB).replace(/\/+$/, "");
  const timeoutMs = options.timeoutMs ?? 15 * 60_000;
  const retries = options.retries ?? 3;
  const backoffMs = options.backoffMs ?? ((attempt: number) => [2_000, 10_000, 30_000][attempt - 1] ?? 30_000);
  const url = new URL(`${base}/v1/chat/completions`);
  const body = JSON.stringify({
    model: question.model,
    messages: question.messages,
    reasoning_effort: question.effort,
    max_tokens: question.maxTokens,
    response_format: { type: "json_schema", json_schema: question.schema },
  });

  for (let attempt = 0; ; attempt++) {
    let failure: HubError;
    let wait = backoffMs(attempt + 1);
    try {
      const reply = await post(url, body, timeoutMs);
      if (reply.status >= 200 && reply.status < 300) return read(reply.body);
      failure = new HubError(`The Hub answered ${reply.status}: ${errorMessage(reply.body)}`, reply.status);
      if (reply.status !== 429 && reply.status !== 503) throw failure;
      const seconds = Number(reply.retryAfter);
      if (reply.retryAfter && Number.isFinite(seconds)) wait = Math.min(Math.max(seconds, 0), 120) * 1000;
    } catch (error) {
      if (error instanceof HubError) throw error;
      if (error instanceof Timeout) {
        throw new HubError(`The Hub did not answer within ${Math.round(timeoutMs / 1000)} seconds`);
      }
      failure = new HubError(`Could not reach the Hub at ${base}: ${(error as Error).message}`);
    }
    if (attempt >= retries) throw failure;
    options.onRetry?.(failure.message, wait);
    await sleep(wait);
  }
}

function read(body: string): Answer {
  let parsed: {
    model?: unknown;
    usage?: Usage;
    choices?: { finish_reason?: unknown; message?: { content?: unknown; refusal?: unknown } }[];
  };
  try {
    parsed = JSON.parse(body) as typeof parsed;
  } catch {
    throw new HubError(`The Hub's answer is not JSON: ${body.trim().slice(0, 300)}`);
  }
  const choice = parsed.choices?.[0];
  if (typeof choice?.message?.refusal === "string" && choice.message.refusal) {
    throw new HubError(`The model refused: ${choice.message.refusal}`);
  }
  if (choice?.finish_reason === "length") {
    throw new HubError("The answer was cut off at max_tokens: raise --max-tokens");
  }
  if (typeof choice?.message?.content !== "string") {
    throw new HubError(`The Hub's answer has no message: ${body.trim().slice(0, 300)}`);
  }
  return {
    content: choice.message.content,
    model: typeof parsed.model === "string" ? parsed.model : "",
    usage: parsed.usage ?? {},
  };
}
