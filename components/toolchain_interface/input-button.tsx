import { Skeleton } from "@/registry/default/ui/skeleton";


export default function InputButton({
    onClick
} : {
    onClick: () => void
}) {
  return (
    <Skeleton className="rounded-md w-24 h-10" />
  )
}


export function InputButtonSkeleton() {
  return (
    <Skeleton className="rounded-md w-24 h-10" />
  )
}