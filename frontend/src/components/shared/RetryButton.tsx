/** Only ever rendered when ErrorDetail.retryable is true - see ErrorPanel. */

import { Button } from "./Button";

export function RetryButton({ onClick, loading }: { onClick: () => void; loading?: boolean }) {
  return (
    <Button variant="secondary" onClick={onClick} loading={loading}>
      Retry
    </Button>
  );
}
