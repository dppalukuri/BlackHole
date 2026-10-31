import type { ComponentChildren } from 'preact';

interface VerdictProps {
  title: string;
  /** Sets the status dot. The title must still say what the status means. */
  tone?: 'neutral' | 'good' | 'warn' | 'bad';
  children?: ComponentChildren;
}

/** The plain-English conclusion at the foot of a calculator's answer. */
export default function Verdict({ title, tone = 'neutral', children }: VerdictProps) {
  return (
    <div class={`verdict tone-${tone}`}>
      <i aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        {children && <p>{children}</p>}
      </div>
    </div>
  );
}
