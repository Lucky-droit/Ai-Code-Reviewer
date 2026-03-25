import type { Issue, Severity } from "../api";

type Props = {
  issues: Issue[];
  onSelectIssue: (line: number) => void;
};

const severityLabel: Record<Severity, string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
};

export default function IssueList({ issues, onSelectIssue }: Props) {
  if (issues.length === 0) {
    return <p className="empty">No issues found. Nice work.</p>;
  }

  return (
    <ul className="issues">
      {issues.map((issue, index) => (
        <li
          key={`${issue.type}-${issue.line}-${index}`}
          className={`issue severity-${issue.severity}`}
          onClick={() => onSelectIssue(issue.line)}
        >
          <div className="issue-top">
            <span className="badge type">{issue.type}</span>
            <span className={`badge severity severity-${issue.severity}`}>
              {severityLabel[issue.severity]}
            </span>
            <span className="line">Line {issue.line}</span>
          </div>
          <p>{issue.message}</p>
        </li>
      ))}
    </ul>
  );
}