import { Badge, Button } from '@mantine/core'
import { PlusIcon, XIcon } from '@phosphor-icons/react'
import type { FC } from 'react'
import type { Language } from '@/types/language'

type LanguageSelectorProps = {
  availableLanguages: Language[]
  selectedLanguages: Language[]
  onAdd: (language: Language) => void
  onRemove: (language: Language) => void
}

const LanguageSelector: FC<LanguageSelectorProps> = ({
  availableLanguages,
  selectedLanguages,
  onAdd,
  onRemove
}) => {
  return (
    <div className="flex flex-col gap-4 py-2">
      {/* Selected Languages */}
      {selectedLanguages.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedLanguages.map((language) => (
            <Badge
              key={language.id}
              color="blue"
              radius="md"
              styles={{
                root: {
                  padding: '4px 12px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }
              }}
              variant="filled"
            >
              <span className="text-sm capitalize">
                {language.language_name}
              </span>
              {selectedLanguages.length > 1 && (
                <Button
                  type="button"
                  variant="subtle"
                  size="xs"
                  styles={{
                    root: {
                      padding: 0,
                      width: '16px',
                      height: '16px',
                      '&:hover': {
                        backgroundColor: '#ef4444',
                        color: '#ffffff'
                      }
                    }
                  }}
                  onClick={() => onRemove(language)}
                  aria-label={`Remove ${language.language_name}`}
                >
                  <XIcon size={12} />
                </Button>
              )}
            </Badge>
          ))}
        </div>
      )}

      {/* Available Languages */}
      <div className="grid gap-2">
        {availableLanguages &&
          availableLanguages.map((language) => (
            <Button
              key={language.id}
              type="button"
              variant="outline"
              onClick={() => onAdd(language)}
              styles={{
                root: {
                  height: '40px',
                  padding: '0 12px',
                  border: '1px solid #e5e7eb',
                  justifyContent: 'space-between',
                  '&:hover': { backgroundColor: '#f9fafb' }
                }
              }}
            >
              <span className="text-sm">{language.language_name}</span>
              <PlusIcon size={16} />
            </Button>
          ))}
      </div>
    </div>
  )
}

export default LanguageSelector
