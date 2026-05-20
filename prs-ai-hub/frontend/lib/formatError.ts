/** Turn httpx/gateway error strings into a short user-facing message. */
export function formatValidationError(raw: string): string {
  const agentMatch = raw.match(/Agent (?:call )?failed \(\d+\): (.+)/);
  if (agentMatch) return simplifyGroqMessage(agentMatch[1]);

  const detailMatch = raw.match(/Agent error: ([\s\S]+)/);
  if (detailMatch) return simplifyGroqMessage(detailMatch[1]);

  if (raw.includes("rate_limit") || raw.includes("429")) {
    return simplifyGroqMessage(raw);
  }

  if (raw.includes("500 Internal Server Error")) {
    return "A validation agent failed. Restart the backend (to load model fallbacks) and resubmit, or check logs.";
  }

  return simplifyGroqMessage(raw);
}

function simplifyGroqMessage(text: string): string {
  if (text.includes("rate_limit") || text.includes("429")) {
    const waitMatch = text.match(/try again in (\d+m[\d.]*s)/i);
    const wait = waitMatch ? ` Try again in ~${waitMatch[1].replace(/m.*/, " minutes")}.` : "";
    return `Groq API daily token limit reached for the primary model.${wait} The backend should auto-fallback to GPT-OSS after restart.`;
  }
  if (text.includes("All Groq models failed")) {
    return text.length > 400 ? `${text.slice(0, 400)}…` : text;
  }
  return text.length > 500 ? `${text.slice(0, 500)}…` : text;
}
