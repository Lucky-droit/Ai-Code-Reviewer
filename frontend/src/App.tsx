import { useMemo, useRef, useState } from "react";
import Editor, { type OnMount } from "@monaco-editor/react";
import type * as Monaco from "monaco-editor";

import { reviewCode, type Issue } from "./api";
import IssueList from "./components/IssueList";

const MAX_CODE_LINES = 500;
const MAX_CODE_CHARS = 25000;

const DEFAULT_CODE = `def process_user(user):
    return user.name.upper()

for i in range(10000):
    print(process_user(None))
`;

const LANGUAGE_OPTIONS = [
  { value: "python", label: "Python" },
  { value: "javascript", label: "JavaScript" },
  { value: "typescript", label: "TypeScript" },
  { value: "java", label: "Java" },
  { value: "go", label: "Go" },
  { value: "cpp", label: "C++" },
];

function severityClassName(severity: Issue["severity"]): string {
  if (severity === "high") return "line-high";
  if (severity === "medium") return "line-medium";
  return "line-low";
}

export default function App() {
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(DEFAULT_CODE);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const editorRef = useRef<Monaco.editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<typeof Monaco | null>(null);
  const decorationsRef = useRef<string[]>([]);

  const lineCount = useMemo(() => code.split("\n").length, [code]);
  const charCount = useMemo(() => code.length, [code]);

  const inputError = useMemo(() => {
    const trimmed = code.trim();
    if (!trimmed) return "Paste code before running review.";
    if (lineCount > MAX_CODE_LINES) {
      return `Code is too long: ${lineCount} lines (max ${MAX_CODE_LINES}).`;
    }
    if (charCount > MAX_CODE_CHARS) {
      return `Code is too long: ${charCount} characters (max ${MAX_CODE_CHARS}).`;
    }
    return null;
  }, [charCount, code, lineCount]);

  const issueCountLabel = useMemo(() => {
    if (issues.length === 0) return "No issues";
    if (issues.length === 1) return "1 issue";
    return `${issues.length} issues`;
  }, [issues.length]);

  const applyDecorations = (nextIssues: Issue[]) => {
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    if (!editor || !monaco) return;

    const model = editor.getModel();
    const maxLine = model?.getLineCount() ?? 1;

    const decorations: Monaco.editor.IModelDeltaDecoration[] = nextIssues.map((issue) => {
      const safeLine = Math.min(Math.max(issue.line, 1), maxLine);
      return {
        range: new monaco.Range(safeLine, 1, safeLine, 1),
        options: {
          isWholeLine: true,
          className: severityClassName(issue.severity),
          glyphMarginClassName: `glyph-${issue.severity}`,
          hoverMessage: { value: `${issue.type.toUpperCase()}: ${issue.message}` },
        },
      };
    });

    decorationsRef.current = editor.deltaDecorations(decorationsRef.current, decorations);
  };

  const handleEditorMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    editor.updateOptions({ glyphMargin: true });
  };

  const handleReview = async () => {
    if (inputError) {
      setError(inputError);
      setIssues([]);
      applyDecorations([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await reviewCode(code, language);
      setIssues(response.issues);
      applyDecorations(response.issues);
    } catch (reviewError) {
      const message = reviewError instanceof Error ? reviewError.message : "Unexpected error.";
      setError(message);
      setIssues([]);
      applyDecorations([]);
    } finally {
      setLoading(false);
    }
  };

  const jumpToLine = (line: number) => {
    const editor = editorRef.current;
    if (!editor) return;
    const safeLine = Math.min(Math.max(line, 1), editor.getModel()?.getLineCount() ?? 1);
    editor.revealLineInCenter(safeLine);
    editor.setPosition({ lineNumber: safeLine, column: 1 });
    editor.focus();
  };

  return (
    <main className="app-shell">
      <section className="panel editor-panel">
        <header className="panel-header">
          <h1>AI Code Reviewer</h1>
          <p>Paste code, run review, and inspect line-level findings.</p>
        </header>

        <div className="controls">
          <label>
            Language
            <select value={language} onChange={(event) => setLanguage(event.target.value)}>
              {LANGUAGE_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <button onClick={handleReview} disabled={loading || Boolean(inputError)}>
            {loading ? "Reviewing..." : "Review Code"}
          </button>
        </div>

        <div className="limits">
          <span>Lines: {lineCount}/{MAX_CODE_LINES}</span>
          <span>Chars: {charCount}/{MAX_CODE_CHARS}</span>
        </div>

        <div className="editor-wrap">
          <Editor
            height="58vh"
            language={language}
            value={code}
            onChange={(value) => setCode(value ?? "")}
            onMount={handleEditorMount}
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbersMinChars: 3,
              tabSize: 2,
              automaticLayout: true,
            }}
          />
        </div>
      </section>

      <section className="panel issues-panel">
        <header className="panel-header">
          <h2>Findings</h2>
          <span className="count">{issueCountLabel}</span>
        </header>

        {error ? <p className="error">{error}</p> : null}

        <IssueList issues={issues} onSelectIssue={jumpToLine} />
      </section>
    </main>
  );
}