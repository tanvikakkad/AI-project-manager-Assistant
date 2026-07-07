import { buildExportCsvUrl } from "../../../api/tasks.api";
import { Button } from "../../../components/Button/Button";
import { useToast } from "../../../components/Toast/ToastContext";
import type { TaskFilters } from "../types";

interface ExportCsvButtonProps {
  filters: TaskFilters;
}

export function ExportCsvButton({ filters }: ExportCsvButtonProps) {
  const { showToast } = useToast();

  function handleExport() {
    showToast("Exporting tasks as CSV…", "success");
    window.location.href = buildExportCsvUrl(filters);
  }

  return (
    <Button variant="secondary" onClick={handleExport}>
      Export CSV
    </Button>
  );
}
