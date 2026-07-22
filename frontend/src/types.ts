export type ItemKind = "origin" | "flag"
export type FlagStatus = "pending" | "approved" | "rejected"
export type EvidenceType = "none" | "source_pbc_table" | "document"

export interface OriginEntry {
  kind: "origin"
  id: string
  blockName: string
  c2Sheet: string
  c2FirstRow: number
  c2LastRow: number
  sourceSheet: string
  sourceFirstRow: number
  sourceLastRow: number
  sampleRows: Record<string, string>[]
}

export interface Candidate {
  docName: string
  score: number
  text: string
  columns?: string[]
  sampleRows?: Record<string, string>[]
  pageCount?: number | null
}

export interface FlaggedItem {
  kind: "flag"
  id: string
  accountName: string
  reason: string
  evidenceType: EvidenceType
  decisionRequired: boolean
  status: FlagStatus
  isDemo?: boolean
  candidates?: Candidate[]
  aiProposal?: string | null
  aiProposalPage?: number | null
  aiProposalUnavailable?: boolean
  aiProposalIsFallback?: boolean
}

export type ReviewRow = OriginEntry | FlaggedItem
