import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { ReviewRow } from "@/types"
import { cn } from "@/lib/utils"

export function ReviewTable({
  rows,
  selectedId,
  onSelect,
}: {
  rows: ReviewRow[]
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>항목명</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => {
          const label = row.kind === "origin" ? row.blockName : row.accountName
          const isSelected = row.id === selectedId
          return (
            <TableRow
              key={row.id}
              onClick={() => onSelect(row.id)}
              className={cn(
                "cursor-pointer transition-colors",
                isSelected && "bg-blue-50 hover:bg-blue-50"
              )}
            >
              <TableCell className={cn("font-medium", isSelected && "text-blue-700")}>{label}</TableCell>
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}
