/*
 * NVIDIA Analyst Chat - Power BI custom visual.
 *
 * Renders a chat panel inside the report and streams answers from the chatbot backend
 * (chatbot/backend, POST /api/chat, Server-Sent Events). The backend holds the Anthropic API key
 * (Azure Key Vault) and queries the NVIDIA Financials semantic model; this visual holds no secret.
 *
 * Network access is declared in capabilities.json ("WebAccess" privilege). BACKEND_URL below must
 * match one of those parameters, and the backend's ALLOWED_ORIGINS must accept the visual's
 * sandboxed iframe origin (browsers send "null").
 *
 * Optional fields: bind Date[fiscal_year] / Date[fiscal_quarter]; when the report filters them to
 * one value, the question is answered for that period.
 */
"use strict";

import powerbi from "powerbi-visuals-api";
import "./../style/visual.less";

import VisualConstructorOptions = powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions = powerbi.extensibility.visual.VisualUpdateOptions;
import IVisual = powerbi.extensibility.visual.IVisual;
import IVisualHost = powerbi.extensibility.visual.IVisualHost;

// Set at build time; must be covered by the WebAccess parameters in capabilities.json.
const BACKEND_URL = "https://nvidia-analyst.example.azurecontainerapps.io";

type Role = "user" | "assistant";
interface Turn { role: Role; content: string; }
interface ReportContext { fiscal_year: number | null; fiscal_quarter: number | null; page: string | null; }
interface EvidenceRow { concept?: string; line_item?: string; period_end?: string; form?: string; accn?: string; sec_url?: string; }
interface Grounding { status?: string; checked?: number; ungrounded?: string[]; }
type ChatEvent =
    | { type: "status"; text: string }
    | { type: "text"; text: string }
    | { type: "evidence"; items: EvidenceRow[] }
    | { type: "done"; grounding?: Grounding; dax_queries?: number }
    | { type: "error"; message: string };

const SUGGESTIONS = [
    "What is NVIDIA's net cash position?",
    "Show revenue for the last 8 quarters",
    "How liquid is the balance sheet?",
];

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
}

/** Render a small, safe subset of markdown (bold, bullet lists, line breaks) with DOM nodes only. */
function renderMarkdown(target: HTMLElement, md: string): void {
    target.replaceChildren();
    let list: HTMLUListElement | null = null;
    for (const line of md.split("\n")) {
        const bullet = /^\s*[-•*]\s+/.test(line);
        const container: HTMLElement = bullet ? (list ??= target.appendChild(el("ul"))).appendChild(el("li")) : target.appendChild(el("p"));
        if (!bullet) list = null;
        const text = bullet ? line.replace(/^\s*[-•*]\s+/, "") : line;
        text.split(/(\*\*[^*]+\*\*)/g).forEach(part => {
            if (part.startsWith("**") && part.endsWith("**") && part.length > 4) container.appendChild(el("strong", undefined, part.slice(2, -2)));
            else if (part) container.appendChild(document.createTextNode(part));
        });
    }
}

export class Visual implements IVisual {
    private readonly host: IVisualHost;
    private readonly root: HTMLElement;
    private readonly log: HTMLElement;
    private readonly input: HTMLTextAreaElement;
    private readonly sendButton: HTMLButtonElement;
    private readonly suggest: HTMLElement;
    private readonly history: Turn[] = [];
    private context: ReportContext = { fiscal_year: null, fiscal_quarter: null, page: null };
    private busy = false;

    constructor(options?: VisualConstructorOptions) {
        if (!options) throw new Error("Visual requires constructor options");
        this.host = options.host;
        this.root = el("div", "nac");
        options.element.appendChild(this.root);

        const header = el("header");
        header.append(el("span", "nac-badge", "AI ANALYST · GROUNDED IN SEC FILINGS"),
                      el("h1", undefined, "Ask about NVIDIA's balance sheet"));
        this.log = el("div", "nac-log");
        this.log.setAttribute("role", "log");
        this.log.setAttribute("aria-live", "polite");

        this.suggest = el("div", "nac-suggest");
        for (const s of SUGGESTIONS) {
            const b = el("button", undefined, s);
            b.type = "button";
            b.onclick = () => { this.input.value = s; void this.ask(); };
            this.suggest.appendChild(b);
        }

        const form = el("form");
        this.input = el("textarea");
        this.input.placeholder = "Ask a question…";
        this.input.setAttribute("aria-label", "Your question");
        this.sendButton = el("button", "nac-send", "Ask");
        this.sendButton.type = "submit";
        form.append(this.input, this.sendButton);
        form.onsubmit = (e) => { e.preventDefault(); void this.ask(); };
        this.input.onkeydown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void this.ask(); } };

        this.root.append(header, this.log, this.suggest, form,
                         el("footer", undefined, "Not investment advice · Source: SEC EDGAR · Powered by Claude"));
    }

    public update(options: VisualUpdateOptions): void {
        // Read the report's period from the optional bound fields (only when filtered to one value).
        const categories = options.dataViews?.[0]?.categorical?.categories ?? [];
        const single = (role: string): number | null => {
            const c = categories.find(cat => cat.source.roles?.[role]);
            const values = c ? Array.from(new Set(c.values.map(v => Number(v)))) : [];
            return values.length === 1 && Number.isFinite(values[0]) ? values[0] : null;
        };
        const fy = single("fiscalYear");
        this.context = { fiscal_year: fy, fiscal_quarter: fy === null ? null : single("fiscalQuarter"), page: null };
    }

    private addMessage(cls: string): HTMLElement {
        const m = el("div", `nac-msg ${cls}`);
        this.log.appendChild(m);
        this.log.scrollTop = this.log.scrollHeight;
        return m;
    }

    private async ask(): Promise<void> {
        const question = this.input.value.trim();
        if (!question || this.busy) return;
        this.busy = true;
        this.sendButton.disabled = true;
        this.input.value = "";
        this.suggest.style.display = "none";
        this.addMessage("user").textContent = question;

        const bot = this.addMessage("bot");
        const status = bot.appendChild(el("div", "nac-status", "Thinking"));
        const body = bot.appendChild(el("div"));
        let answer = "";

        try {
            const res = await fetch(`${BACKEND_URL}/api/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question, history: this.history, report_context: this.context }),
            });
            if (!res.ok || !res.body) throw new Error(res.status === 429 ? "Too many questions - wait a minute." : `Request failed (${res.status})`);
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            for (;;) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                let i: number;
                while ((i = buffer.indexOf("\n\n")) >= 0) {
                    const chunk = buffer.slice(0, i);
                    buffer = buffer.slice(i + 2);
                    if (!chunk.startsWith("data: ")) continue;
                    const ev = JSON.parse(chunk.slice(6)) as ChatEvent;
                    if (ev.type === "status") status.textContent = ev.text;
                    else if (ev.type === "text") { answer += ev.text; renderMarkdown(body, answer); this.log.scrollTop = this.log.scrollHeight; }
                    else if (ev.type === "evidence") bot.appendChild(this.renderEvidence(ev.items));
                    else if (ev.type === "done") { status.remove(); bot.appendChild(this.renderMeta(ev.grounding, ev.dax_queries ?? 0)); }
                    else if (ev.type === "error") { status.remove(); bot.appendChild(el("p", "nac-error", ev.message)); }
                }
            }
            if (answer) this.history.push({ role: "user", content: question }, { role: "assistant", content: answer });
        } catch (err) {
            status.remove();
            bot.appendChild(el("p", "nac-error", err instanceof Error ? err.message : "Request failed"));
        } finally {
            this.busy = false;
            this.sendButton.disabled = false;
        }
    }

    private renderEvidence(items: EvidenceRow[]): HTMLElement {
        const box = el("div", "nac-sources");
        box.appendChild(el("strong", undefined, "SEC evidence"));
        for (const r of items) {
            const row = el("div");
            row.appendChild(document.createTextNode(`${r.line_item ?? r.concept ?? ""} · ${String(r.period_end ?? "").slice(0, 10)} · ${r.form ?? ""} · `));
            const url = r.sec_url ?? "";
            if (/^https:\/\/www\.sec\.gov\//.test(url)) {
                const a = el("a", undefined, r.accn ?? "filing");
                a.href = "#";
                // Visuals must open links through the host (launchUrl), not navigate the sandbox.
                a.onclick = (e) => { e.preventDefault(); this.host.launchUrl(url); };
                row.appendChild(a);
            } else {
                row.appendChild(document.createTextNode(r.accn ?? ""));
            }
            box.appendChild(row);
        }
        return box;
    }

    private renderMeta(g: Grounding | undefined, daxQueries: number): HTMLElement {
        const meta = el("div", "nac-meta");
        if (g?.status === "verified") meta.appendChild(el("span", "nac-chip ok", `✓ ${g.checked} FIGURES VERIFIED`));
        else if (g?.status === "unverified") {
            const chip = el("span", "nac-chip warn", `⚠ ${g.ungrounded?.length ?? 0} FIGURE(S) NOT IN THE DATA`);
            chip.title = (g.ungrounded ?? []).join(", ");
            meta.appendChild(chip);
        }
        meta.appendChild(el("span", "nac-chip", `${daxQueries} DAX ${daxQueries === 1 ? "QUERY" : "QUERIES"}`));
        return meta;
    }
}
