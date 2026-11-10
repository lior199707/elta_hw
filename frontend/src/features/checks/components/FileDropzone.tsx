import { useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'

import { cn } from '@/lib/utils'
import { formatFileSize } from '@/lib/utils/formatDisplayValues'

import { DOCUMENT_ACCEPT_ATTRIBUTE } from '../schemas/documentFile.schema'

interface FileDropzoneProps {
  file: File | null
  error: string | null
  disabled: boolean
  onFileSelected: (file: File) => void
}

export function FileDropzone({ file, error, disabled, onFileSelected }: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0]
    if (selected) {
      onFileSelected(selected)
    }
    event.target.value = ''
  }

  const handleDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault()
    setIsDragging(false)
    const dropped = event.dataTransfer.files[0]
    if (!disabled && dropped) {
      onFileSelected(dropped)
    }
  }

  return (
    <div className="space-y-2">
      <label
        onDragOver={(event) => {
          event.preventDefault()
          if (!disabled) {
            setIsDragging(true)
          }
        }}
        onDragLeave={() => {
          setIsDragging(false)
        }}
        onDrop={handleDrop}
        className={cn(
          'flex cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed p-8 text-center transition-colors focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-indigo-600',
          isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 bg-white',
          error ? 'border-red-400' : null,
          disabled ? 'cursor-not-allowed opacity-60' : 'hover:border-indigo-400',
        )}
      >
        <span className="font-medium text-slate-900">Document</span>
        <span className="text-sm text-slate-600">
          Drag and drop a .docx or .txt file here, or click to choose one (max 20 MB)
        </span>
        <input
          type="file"
          className="sr-only"
          accept={DOCUMENT_ACCEPT_ATTRIBUTE}
          disabled={disabled}
          onChange={handleChange}
          aria-describedby={error ? 'document-error' : undefined}
        />
      </label>
      {file ? (
        <p className="text-sm text-slate-700">
          Selected: <span className="font-medium">{file.name}</span> ({formatFileSize(file.size)})
        </p>
      ) : null}
      {error ? (
        <p id="document-error" role="alert" className="text-sm text-red-700">
          {error}
        </p>
      ) : null}
    </div>
  )
}
