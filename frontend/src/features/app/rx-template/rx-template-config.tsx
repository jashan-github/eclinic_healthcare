import { type FC, type ChangeEvent, useEffect, useState } from 'react'
import { Button, NativeSelect } from '@mantine/core'
import { CaretDownIcon } from '@phosphor-icons/react'
import { toast } from 'react-toastify'
import GlobalLoader from '@/components/orvo/common/global-loader'
import { useClinics } from '@/hooks/use-doctor-template-clinic'
import { useMyProfile } from '../my-profile/hooks/use-my-profile'
import { useSaveRxTemplate, useRxTemplate } from '@/hooks/use-rx-template'
import type { SaveRxTemplatePayload } from '@/services/rx-template-service'

const RxTemplateConfig: FC = () => {
  const [selectedClinic, setSelectedClinic] = useState<string>('')
  const [letterheadFile, setLetterheadFile] = useState<File | null>(null)
  const [isDefaultActive, setIsDefaultActive] = useState(false)
  const [currentTemplateId, setCurrentTemplateId] = useState<string | null>(null)
  const { mutate: saveTemplate } = useSaveRxTemplate()

  const { data, isLoading } = useClinics()
  const { myProfile } = useMyProfile()
  const selectedClinicData = data?.locations.find(c => c.name === selectedClinic)
  const liveAddress = selectedClinicData?.address || 'Address not available'

  const { data: savedTemplate, refetch: refetchLetterhead } = useRxTemplate(selectedClinicData?.id)

  const truncateName = (name: string, len = 28) =>
    name.length > len ? name.slice(0, len - 3) + '...' : name

  // Auto-select first clinic location by default
  useEffect(() => {
    if (data?.locations?.length && !selectedClinic) {
      const primaryLocation = data.locations.find(loc => loc.is_primary) || data.locations[0]
      setSelectedClinic(primaryLocation.name)
    }
  }, [data?.locations, selectedClinic])

  useEffect(() => {
    if (isDefaultActive && selectedClinic) {
      window.__LETTERHEAD__ = {
        type: 'default',
        doctorName: `${myProfile.full_name}`,
        qualification: `${myProfile.education}`,
        clinicAddress: liveAddress,
      }
      window.dispatchEvent(new Event('letterheadChanged'))
    }
  }, [selectedClinic, liveAddress, isDefaultActive, myProfile])

  // Fetch new letterhead when dropdown changes
  useEffect(() => {
    refetchLetterhead()
    setLetterheadFile(null)
    setIsDefaultActive(false)
    window.__LETTERHEAD__ = null
    window.dispatchEvent(new Event('letterheadChanged'))
  }, [selectedClinic, selectedClinicData?.id, refetchLetterhead])

  // Load fetched letterhead into preview
  useEffect(() => {
    if (savedTemplate?.data?.templates?.length) {
      const templates = savedTemplate.data.templates
      const defaultTemplate = templates.find(t => t.is_default) || templates[0]
      console.log("templates", defaultTemplate)
      setCurrentTemplateId(defaultTemplate.id)

      const { letterhead_image_url, updated_at } = defaultTemplate

      if (letterhead_image_url) {
        setIsDefaultActive(false)
        setLetterheadFile(null)
        
        // ✅ ADD CACHE BUSTER: Append timestamp to prevent browser caching
        const cacheBustedUrl = `${letterhead_image_url}?v=${new Date(updated_at).getTime()}`
        window.__LETTERHEAD__ = cacheBustedUrl
      } else {
        setIsDefaultActive(true)
        setLetterheadFile(null)
        window.__LETTERHEAD__ = {
          type: 'default',
          doctorName: `${myProfile.full_name}`,
          qualification: `${myProfile.education}`,
          clinicAddress: liveAddress,
        }
      }
      window.dispatchEvent(new Event('letterheadChanged'))
    } else {
      setCurrentTemplateId(null)
      setIsDefaultActive(false)
      setLetterheadFile(null)
      window.__LETTERHEAD__ = {
        type: 'default',
        doctorName: `${myProfile.full_name}`,
        qualification: `${myProfile.education}`,
        clinicAddress: liveAddress,
      }
      window.dispatchEvent(new Event('letterheadChanged'))
    }
  }, [savedTemplate, myProfile, liveAddress])

  const handleUseDefault = () => {
    setLetterheadFile(null)
    setIsDefaultActive(true)
    window.__LETTERHEAD__ = {
      type: 'default',
      doctorName: `${myProfile.full_name}`,
      qualification: `${myProfile.education}`,
      clinicAddress: liveAddress,
    }
    window.dispatchEvent(new Event('letterheadChanged'))
  }

  const handleUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setLetterheadFile(file)
    setIsDefaultActive(false)
    const reader = new FileReader()
    reader.onload = () => {
      window.__LETTERHEAD__ = reader.result as string
      window.dispatchEvent(new Event('letterheadChanged'))
    }
    reader.readAsDataURL(file)
  }

  const handleReset = () => {
    setLetterheadFile(null)
    setIsDefaultActive(false)
    refetchLetterhead()

    if (savedTemplate?.data?.templates?.length) {
      const templates = savedTemplate.data.templates
      const defaultTemplate = templates.find(t => t.is_default) || templates[0]
      const { letterhead_image_url, updated_at } = defaultTemplate

      if (letterhead_image_url) {
        // ✅ ADD CACHE BUSTER on reset too
        const cacheBustedUrl = `${letterhead_image_url}?v=${new Date(updated_at).getTime()}`
        window.__LETTERHEAD__ = cacheBustedUrl
      } else {
        window.__LETTERHEAD__ = {
          type: 'default',
          doctorName: `${myProfile.full_name}`,
          qualification: `${myProfile.education}`,
          clinicAddress: liveAddress,
        }
      }
    } else {
      window.__LETTERHEAD__ = null
    }

    window.dispatchEvent(new Event('letterheadChanged'))
    toast.info('Reset to saved template')
  }

  const handleSave = () => {
    if (!data?.locations?.length) {
      toast.error('Clinic locations not loaded yet!')
      return
    }

    const finalClinicName = selectedClinic || data.locations[0].name
    const selectedClinicObj = data.locations.find(c => c.name === finalClinicName)

    if (!selectedClinicObj) {
      toast.error('Selected clinic location not found!')
      return
    }

    const payload: SaveRxTemplatePayload & { templateId?: string } = {
      clinic_location_id: selectedClinicObj.id,
      use_default_letterhead: !letterheadFile,
      letterhead: letterheadFile || undefined,
      templateId: currentTemplateId ?? undefined,
    }

    console.log('Sending to backend →', payload)
    saveTemplate(payload, {
      onSuccess: () => {
        // ✅ Force refetch after successful save to get updated timestamp
        setTimeout(() => {
          refetchLetterhead()
        }, 500)
      }
    })
  }

  useEffect(() => {
    if (!isLoading && data?.locations?.length && !selectedClinic) {
      const primaryLocation = data.locations.find(loc => loc.is_primary) || data.locations[0]
      setSelectedClinic(primaryLocation.name)
    }
  }, [isLoading, data?.locations, selectedClinic])

  return (
    <div className="flex flex-col gap-sm h-full bg-white border border-1 border-gray-300 shadow-lg">
      <Button fullWidth radius={0} size="lg" onClick={() => window.print()}>
        Print Rx Template
      </Button>

      <div>
        <div className="p-4">
          <NativeSelect
            data={isLoading ? ['Loading...'] : data?.locations.map(c => c.name) || []}
            label="Select Clinic Location"
            value={selectedClinic}
            onChange={(e) => setSelectedClinic(e.currentTarget.value || '')}
            disabled={isLoading}
            rightSection={isLoading ? <GlobalLoader /> : <CaretDownIcon weight="fill" />}
          />
        </div>

        {/* <Divider /> */}

        <div className="flex flex-col gap-sm p-4">
          <label className="cursor-pointer">
            <input
              type="file"
              accept="image/jpg,image/jpeg,image/png,image/gif,image/webp"
              className="hidden"
              onChange={handleUpload}
            />
            <div className="bg-white h-16 py-2 px-4 border border-gray-300 rounded flex flex-col gap-2 hover:border-blue-400 transition">
              <div className="font-medium text-sm">
                {letterheadFile ? truncateName(letterheadFile.name) : 'Upload Letterhead'}
              </div>
              <div className="text-gray-600 text-xs">JPG, JPEG, PNG, GIF, WEBP (max 5MB)</div>
            </div>
          </label>

          <div className="font-semibold flex justify-center items-center">OR</div>

          <button
            onClick={handleUseDefault}
            className="bg-white h-16 py-2 px-4 border border-gray-300 rounded flex items-center gap-2 hover:border-blue-400 transition cursor-pointer"
          >
            <div className="font-medium text-sm">Use Default</div>
          </button>

          <div className="flex justify-between items-center mt-6">
            <Button bg="white" variant="outline" onClick={handleReset}>
              Reset
            </Button>
            <Button
              variant="filled"
              onClick={handleSave}
              disabled={!selectedClinic || isLoading}
            >
              Save
            </Button>
          </div>
        </div>

      </div>
    </div>
  )
}

export default RxTemplateConfig