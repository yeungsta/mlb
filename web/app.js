import { Client } from "@langchain/langgraph-sdk/client";
import DOMPurify from "dompurify";
import { marked } from "marked";
import "./styles.css";

const client = new Client({
  apiUrl: new URL("/langgraph", window.location.origin).href,
});
const starters = [
  ["Scout a pitcher", "Analyze Trevor Megill’s pitching this season and summarize his pitch mix."],
  ["Scout a hitter", "Analyze Tommy Edman’s batting, recent exit velocity, and 2025 wOBA and xwOBA."],
  ["Batter vs. pitcher", "Compare Mike Trout and Clayton Kershaw in their historical head-to-head matchups."],
  ["Starter vs. lineup", "Analyze the Dodgers’ starting pitcher against the Yankees’ lineup on October 25, 2024."],
  ["Look up a game", "Who started the October 25, 2024 Dodgers–Yankees game, and what were both batting orders?"],
];

const composer = document.querySelector("#composer");
const prompt = document.querySelector("#prompt");
const conversation = document.querySelector("#conversation");
const answerTemplate = document.querySelector("#answer-template");
const send = document.querySelector("#send");
const newChat = document.querySelector("#new-chat");

let threadId;
let running = false;

for (const [label, example] of starters) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "secondary";
  button.textContent = label;
  button.addEventListener("click", () => {
    prompt.value = example;
    prompt.focus();
  });
  document.querySelector("#starters").append(button);
}

newChat.addEventListener("click", () => {
  threadId = undefined;
  conversation.replaceChildren();
  prompt.value = "";
  prompt.focus();
});

function renderMarkdown(element, value) {
  element.innerHTML = DOMPurify.sanitize(marked.parse(value), {
    ALLOWED_TAGS: [
      "p", "strong", "em", "del", "a", "blockquote", "ul", "ol", "li", "br", "hr",
      "h1", "h2", "h3", "h4", "h5", "h6", "pre", "code",
      "table", "thead", "tbody", "tr", "th", "td",
    ],
    ALLOWED_ATTR: ["href", "title", "start"],
  });
}

function addTrace(answer, text) {
  const details = answer.querySelector(".trace");
  const item = document.createElement("li");
  item.textContent = text;
  details.querySelector("ul").append(item);
  details.hidden = false;
}

composer.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = prompt.value.trim();
  if (running || !question) return;

  running = true;
  send.disabled = true;
  newChat.disabled = true;
  prompt.value = "";

  const userMessage = document.createElement("p");
  userMessage.className = "question";
  userMessage.textContent = question;
  const answer = answerTemplate.content.firstElementChild.cloneNode(true);
  const status = answer.querySelector(".status");
  const progress = answer.querySelector("progress");
  status.textContent = "Starting run…";
  conversation.append(userMessage, answer);
  userMessage.scrollIntoView({ block: "nearest" });

  const result = { title: "", summary: "", stats: "" };
  const setProgress = (message, value) => {
    if (status.textContent !== message) status.textContent = message;
    if (typeof value === "number") progress.value = value * 100;
  };

  try {
    if (!threadId) {
      const thread = await client.threads.create();
      threadId = thread.thread_id;
    }

    const stream = client.runs.stream(threadId, "vin-ai", {
      input: { messages: [{ type: "human", content: question }] },
      streamMode: ["custom", "updates"],
    });

    for await (const { event: kind, data } of stream) {
      if (kind === "error") {
        throw new Error(data?.message || "The LangGraph run failed.");
      }

      if (kind === "custom" && typeof data?.message === "string") {
        setProgress(data.message, data.progress);
      }

      if (kind !== "updates") continue;

      if (data.stat_retrieval) {
        result.stats = data.stat_retrieval.stats_summary ?? "";
        for (const message of data.stat_retrieval.messages ?? []) {
          for (const call of message.tool_calls ?? []) {
            addTrace(answer, call.name);
          }
        }
      }

      for (const message of data.tool_caller?.messages ?? []) {
        if (message.status === "error") {
          addTrace(answer, `${message.name ?? "Tool"} failed`);
        }
      }

      if (data.matchup_synthesizer) {
        result.summary = data.matchup_synthesizer.summary ?? "";
      }
      if (data.title_maker) {
        result.title = data.title_maker.title ?? "";
      }
    }

    if (result.summary) {
      const title = answer.querySelector(".report-title");
      title.textContent = result.title || "Matchup report";
      title.hidden = false;
      renderMarkdown(answer.querySelector(".report"), result.summary);
      setProgress("Report complete", 1);
    } else {
      setProgress(result.stats ? "Retrieved stats · No report generated" : "No report generated", 1);
    }

    if (result.stats) {
      renderMarkdown(answer.querySelector(".stats-content"), result.stats);
      answer.querySelector(".stats").hidden = false;
      if (!result.summary) answer.querySelector(".stats").open = true;
    }
  } catch (error) {
    setProgress("Run failed");
    addTrace(answer, error instanceof Error ? error.message : String(error));
    answer.querySelector(".trace").open = true;
  } finally {
    progress.hidden = true;
    running = false;
    send.disabled = false;
    newChat.disabled = false;
  }
});
