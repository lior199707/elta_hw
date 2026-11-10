const MS_PER_SECOND = 1000
const SECONDS_PER_MINUTE = 60
const BYTES_PER_KB = 1024
const BYTES_PER_MB = BYTES_PER_KB * 1024
const DECIMALS_KEEP_THRESHOLD = 10

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
})

export function formatDateTime(isoString: string): string {
  const date = new Date(isoString)
  if (Number.isNaN(date.getTime())) {
    throw new Error(`Invalid ISO date: ${isoString}`)
  }
  return dateTimeFormatter.format(date)
}

export function formatDuration(durationMs: number): string {
  if (durationMs < MS_PER_SECOND) {
    return `${Math.round(durationMs)} ms`
  }
  const totalSeconds = durationMs / MS_PER_SECOND
  if (totalSeconds < SECONDS_PER_MINUTE) {
    return `${totalSeconds.toFixed(1)} s`
  }
  const minutes = Math.floor(totalSeconds / SECONDS_PER_MINUTE)
  const seconds = Math.round(totalSeconds - minutes * SECONDS_PER_MINUTE)
  return `${minutes} min ${seconds} s`
}

export function formatFileSize(bytes: number): string {
  if (bytes < BYTES_PER_KB) {
    return `${bytes} B`
  }
  if (bytes < BYTES_PER_MB) {
    return `${(bytes / BYTES_PER_KB).toFixed(1)} KB`
  }
  const megabytes = bytes / BYTES_PER_MB
  return `${megabytes.toFixed(megabytes < DECIMALS_KEEP_THRESHOLD ? 1 : 0)} MB`
}
