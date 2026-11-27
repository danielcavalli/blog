// What the tests share: a repository of their own to work in, and a Hub that answers what they say.
// No test reaches the real Hub.

import fs from "node:fs";
import http from "node:http";
import type { AddressInfo } from "node:net";
import os from "node:os";
import path from "node:path";

/** A repository of its own, in a temporary folder, with these files. */
export function repository(files: Record<string, string>): string {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "translate-test-"));
  for (const [name, content] of Object.entries(files)) {
    fs.mkdirSync(path.dirname(path.join(root, name)), { recursive: true });
    fs.writeFileSync(path.join(root, name), content);
  }
  return root;
}

export interface Asked {
  model: string;
  messages: { role: string; content: string }[];
  reasoning_effort: string;
  max_tokens: number;
  response_format: { type: string; json_schema: { name: string; schema: Record<string, unknown> } };
}

/** What the fake Hub sends back: the model's answer (any value is sent as JSON), or an error with its status. */
export type Reply = { answer: unknown; cost?: number } | { status: number; message: string };

export interface FakeHub {
  baseUrl: string;
  /** Every question asked, in order. */
  asked: Asked[];
  /** The replies still to give, in order. A question with no reply left gets a 500. */
  replies: Reply[];
  close: () => Promise<void>;
}

/** A local server that speaks the Hub's `/v1/chat/completions`. */
export async function fakeHub(): Promise<FakeHub> {
  const hub: FakeHub = { baseUrl: "", asked: [], replies: [], close: async () => {} };
  const server = http.createServer((request, response) => {
    const chunks: Buffer[] = [];
    request.on("data", (chunk: Buffer) => chunks.push(chunk));
    request.on("end", () => {
      hub.asked.push(JSON.parse(Buffer.concat(chunks).toString("utf8")) as Asked);
      const reply = hub.replies.shift() ?? { status: 500, message: "the test queued no reply" };
      const send = (status: number, value: unknown) => {
        response.writeHead(status, { "content-type": "application/json" });
        response.end(JSON.stringify(value));
      };
      if ("status" in reply) return send(reply.status, { error: { message: reply.message } });
      send(200, {
        model: hub.asked.at(-1)!.model,
        choices: [
          {
            finish_reason: "stop",
            message: { role: "assistant", content: typeof reply.answer === "string" ? reply.answer : JSON.stringify(reply.answer) },
          },
        ],
        usage: { prompt_tokens: 1000, completion_tokens: 200, total_tokens: 1200, cost_usd: reply.cost ?? 0.01 },
      });
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  hub.baseUrl = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  hub.close = () =>
    new Promise((resolve) => {
      server.closeAllConnections();
      server.close(() => resolve());
    });
  return hub;
}
