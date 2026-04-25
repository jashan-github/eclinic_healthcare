// location-cards.tsx
import React, { useState } from 'react'
import { LocationItem } from './location-item'
import { toast } from 'react-toastify'
import EditLocationDialog from './edit-location-dialog'
import { useLocations } from './hooks/use-location'

export const LocationCards: React.FC = () => {
  const { data, isLoading, error, deleteLocation } = useLocations()

  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedLocation, setSelectedLocation] = useState<any>(null)

  const handleOpenEdit = (location: any) => {
    setSelectedLocation(location)
    setIsEditDialogOpen(true)
  }

  const handleDelete = (id: string, name: string) => {
    deleteLocation(id, {
      onSuccess: () => {
        toast.success(`${name} deleted successfully!`)
      },
      onError: (error: any) => {
        toast.error(error?.message || 'Failed to delete location')
      }
    })
  }

  // Loading, error, empty states (same as before)
  if (isLoading) {
    return (
      <div className="p-8 text-center">
        <p className="text-[#64748B] font-poppins text-lg">Loading locations...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-600 font-poppins text-lg">Failed to load locations. Please try again.</p>
      </div>
    )
  }

  if (!data?.locations || data.locations.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-[#64748B] font-poppins text-lg">No locations found.</p>
      </div>
    )
  }

  return (
    <div className="p-4 bg-[#F4F6F9] grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
      {data.locations.map((location) => (
        <LocationItem
          key={location.id}
          location={{
            title: location.name,
            address: location.address,
            phone: location.phone || 'N/A',
            email: location.email || 'N/A',
            branch: location.branch_type,
          }}
          onEdit={() => handleOpenEdit(location)}
          onDelete={() => handleDelete(location.id, location.name)}
        />
      ))}

      {/* Edit Dialog Only */}
      {selectedLocation && (
        <EditLocationDialog
          isOpen={isEditDialogOpen}
          onClose={() => setIsEditDialogOpen(false)}
          initialData={selectedLocation}
        />
      )}
    </div>
  )
}

export default LocationCards