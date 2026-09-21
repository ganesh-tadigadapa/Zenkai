import { Badge } from "@/components/ui/Badge";
import { IconAward } from "@/components/ui/Icons";
import {
  ASSESSMENT_LABELS,
  CREDENTIAL_TYPE_LABELS,
  DELIVERY_LABELS,
  LEVEL_LABELS,
  PROCTORED_LABELS,
  specializationLabel,
} from "@/lib/format";
import type { Credential } from "@/lib/types";

/**
 * What the student actually ends up holding, and how they get it.
 *
 * Unstated fields are shown as "Not stated" rather than hidden. A gap is
 * information: it tells a student the provider has not published something,
 * which is different from the answer being no. Hiding it would leave them
 * assuming the opposite.
 */
function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="border-b border-border py-2.5 last:border-0">
      <dt className="text-[11px] font-semibold uppercase tracking-[0.07em] text-faint">{label}</dt>
      <dd className="mt-0.5 text-[13px] leading-relaxed text-text">{children}</dd>
    </div>
  );
}

function Unstated() {
  return <span className="text-faint">Not stated by the provider</span>;
}

export function CredentialPanel({ credential }: { credential: Credential }) {
  const proctoringUnknown = credential.proctored_status === "unknown";

  return (
    <section
      aria-labelledby="credential-heading"
      className="rounded-panel border border-border bg-surface p-5"
    >
      <h2
        id="credential-heading"
        className="flex items-center gap-2 text-[13px] font-semibold text-text"
      >
        <IconAward className="text-[15px] text-faint" />
        What you earn
      </h2>

      <dl className="mt-2">
        <Row label="Credential">
          {credential.credential_type === "unknown" ? (
            <Unstated />
          ) : (
            CREDENTIAL_TYPE_LABELS[credential.credential_type]
          )}
        </Row>

        {credential.issuer ? <Row label="Issued by">{credential.issuer}</Row> : null}

        {credential.exam_code ? (
          <Row label="Exam code">
            <span className="font-mono text-[12.5px]">{credential.exam_code}</span>
          </Row>
        ) : null}

        <Row label="Assessment">
          {credential.assessment_type === "unknown" ? (
            <Unstated />
          ) : (
            ASSESSMENT_LABELS[credential.assessment_type]
          )}
        </Row>

        <Row label="Proctoring">
          {proctoringUnknown ? (
            <>
              <Unstated />
              <span className="mt-0.5 block text-[11.5px] leading-relaxed text-faint">
                Zenkai does not assume an exam is unproctored just because nobody said so. Check
                the official source if this matters to you.
              </span>
            </>
          ) : (
            PROCTORED_LABELS[credential.proctored_status]
          )}
        </Row>

        <Row label="Delivery">
          {credential.delivery_mode === "unknown" ? (
            <Unstated />
          ) : (
            DELIVERY_LABELS[credential.delivery_mode]
          )}
        </Row>

        <Row label="Level">
          {credential.experience_level === "unknown" ? (
            <Unstated />
          ) : (
            LEVEL_LABELS[credential.experience_level]
          )}
        </Row>

        {credential.duration_hours ? (
          <Row label="Study time">About {credential.duration_hours} hours</Row>
        ) : null}

        {credential.validity_months ? (
          <Row label="Valid for">
            {credential.validity_months % 12 === 0
              ? `${credential.validity_months / 12} year${credential.validity_months > 12 ? "s" : ""}`
              : `${credential.validity_months} months`}
          </Row>
        ) : null}

        {credential.specializations.length > 0 ? (
          <Row label="Subject areas">
            <span className="mt-1 flex flex-wrap gap-1.5">
              {credential.specializations.map((value) => (
                <Badge key={value} tone="neutral">
                  {specializationLabel(value)}
                </Badge>
              ))}
            </span>
          </Row>
        ) : null}
      </dl>
    </section>
  );
}

/** One compact badge for the card: what the student ends up holding. */
export function CredentialBadge({ credential }: { credential: Credential }) {
  if (credential.credential_type === "unknown") return null;
  return (
    <Badge
      tone="neutral"
      title={
        credential.exam_code
          ? `${CREDENTIAL_TYPE_LABELS[credential.credential_type]} · exam ${credential.exam_code}`
          : CREDENTIAL_TYPE_LABELS[credential.credential_type]
      }
    >
      <IconAward />
      {CREDENTIAL_TYPE_LABELS[credential.credential_type]}
    </Badge>
  );
}
