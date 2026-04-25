// components/e-clinic/admin/location/add-location-dialog.tsx
import { useLocation } from '@/features/app/my-profile/hooks/use-locations'
import { XIcon } from '@phosphor-icons/react'
import React, { useState } from 'react'
import { toast } from 'react-toastify'
import { useLocations } from './hooks/use-location'

interface AddLocationDialogProps {
    isOpen: boolean
    onClose: () => void
}

const AddLocationDialog: React.FC<AddLocationDialogProps> = ({ isOpen, onClose }) => {
    if (!isOpen) return null

    const [selectedCountryId, setSelectedCountryId] = useState('')
    const [selectedStateId, setSelectedStateId] = useState('')
    const [selectedCityId, setSelectedCityId] = useState('')

    const {
        countries,
        states,
        cities,
        isLoadingCountries,
        isLoadingStates,
        isLoadingCities
    } = useLocation(selectedCountryId, selectedStateId)

    const { createLocation, isCreating } = useLocations()

    const [formData, setFormData] = useState({
        clinicName: '',
        branchName: '',
        address: '',
        countryId: '',
        stateId: '',
        cityId: '',
        phone: '',
        email: '',
        isPrimary: false,
    })

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        })
    }

    // Save button disable logic
    const isFormValid =
        formData.clinicName.trim() !== '' &&
        formData.branchName.trim() !== '' &&
        formData.address.trim() !== '' &&
        formData.countryId !== '' &&
        formData.stateId !== '' &&
        formData.cityId !== ''

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()

        const payload: {
            name: string
            branch_type: string
            address: string
            country_id: string
            state_id: string
            city_id: string
            phone?: string
            email?: string
            is_primary: boolean
        } = {
            name: formData.clinicName,
            branch_type: formData.branchName || 'Main Branch',
            address: formData.address,
            country_id: formData.countryId,
            state_id: formData.stateId,
            city_id: formData.cityId,
            is_primary: formData.isPrimary,
        }

        if (formData.phone.trim()) {
            payload.phone = formData.phone.trim()
        }
        if (formData.email.trim()) {
            payload.email = formData.email.trim()
        }

        createLocation(payload, {
            onSuccess: () => {
                toast.success('Location added successfully!')
                onClose()
            },
            onError: (error: any) => {
                toast.error(error.message || 'Failed to add location')
            }
        })
    }

    return (
        <div className="fixed inset-0 z-[9999]" onClick={onClose}>
            <div className="absolute inset-0 bg-black/60" />

            <div className="relative h-full w-full flex items-center justify-center p-4">
                <div
                    className="bg-white rounded-2xl shadow-2xl"
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="flex items-center justify-between px-6 py-3">
                        <div className="font-poppins font-normal text-sm text-[#0F1011]">
                            Add New Location
                        </div>
                        <button
                            onClick={onClose}
                            className="p-1 hover:bg-gray-100 rounded-full"
                        >
                            <XIcon size={20} weight="bold" className="text-gray-600" />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="p-6 space-y-5">
                        <div>
                            <label className="font-poppins text-sm text-[#0F1011] block mb-2">Clinic Name</label>
                            <input
                                type="text"
                                name="clinicName"
                                value={formData.clinicName}
                                onChange={handleChange}
                                className="w-full px-4 py-3 border border-gray-300 rounded-md"
                                required
                            />
                        </div>

                        <div>
                            <label className="font-poppins text-sm text-[#0F1011] block mb-2">Branch Name</label>
                            <input
                                type="text"
                                name="branchName"
                                value={formData.branchName}
                                onChange={handleChange}
                                className="w-full px-4 py-3 border border-gray-300 rounded-md"
                            />
                        </div>

                        <div>
                            <label className="font-poppins text-sm text-[#0F1011] block mb-2">Address</label>
                            <input
                                type="text"
                                name="address"
                                value={formData.address}
                                onChange={handleChange}
                                className="w-full px-4 py-3 border border-gray-300 rounded-md"
                                required
                            />
                        </div>

                        <div className="grid grid-cols-3 gap-4">
                            <div>
                                <label className="font-poppins text-sm text-[#0F1011] block mb-2">Country</label>
                                <select
                                    value={selectedCountryId}
                                    onChange={(e) => {
                                        const id = e.target.value
                                        setSelectedCountryId(id)
                                        setFormData({
                                            ...formData,
                                            countryId: id,
                                            stateId: '',
                                            cityId: ''
                                        })
                                        setSelectedStateId('')
                                        setSelectedCityId('')
                                    }}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-md"
                                    required
                                >
                                    <option value="">{isLoadingCountries ? 'Loading...' : 'Select country'}</option>
                                    {countries.map(country => (
                                        <option key={country.id} value={country.id}>
                                            {country.name}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="font-poppins text-sm text-[#0F1011] block mb-2">State</label>
                                <select
                                    value={selectedStateId}
                                    onChange={(e) => {
                                        const id = e.target.value
                                        setSelectedStateId(id)
                                        setFormData({
                                            ...formData,
                                            stateId: id,
                                            cityId: ''
                                        })
                                        setSelectedCityId('')
                                    }}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-md"
                                    disabled={!selectedCountryId}
                                    required
                                >
                                    <option value="">{isLoadingStates ? 'Loading...' : 'Select state'}</option>
                                    {states.map(state => (
                                        <option key={state.id} value={state.id}>
                                            {state.name}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="font-poppins text-sm text-[#0F1011] block mb-2">City</label>
                                <select
                                    value={selectedCityId}
                                    onChange={(e) => {
                                        const id = e.target.value
                                        setSelectedCityId(id)
                                        setFormData({ ...formData, cityId: id })
                                    }}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-md"
                                    disabled={!selectedStateId}
                                    required
                                >
                                    <option value="">{isLoadingCities ? 'Loading...' : 'Select city'}</option>
                                    {cities.map(city => (
                                        <option key={city.id} value={city.id}>
                                            {city.name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="font-poppins text-sm text-[#0F1011] block mb-2">Phone</label>
                                <input
                                    type="number"
                                    name="phone"
                                    value={formData.phone}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-md [appearance:textfield] [&::-webkit-outer-spin-button]:hidden [&::-webkit-inner-spin-button]:hidden"
                                />
                            </div>
                            <div>
                                <label className="font-poppins text-sm text-[#0F1011] block mb-2">Email</label>
                                <input
                                    type="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-md"
                                />
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            <input
                                type="checkbox"
                                checked={formData.isPrimary}
                                onChange={(e) => setFormData({ ...formData, isPrimary: e.target.checked })}
                                className="h-4 w-4 accent-[#002FD4]"
                            />
                            <span className="font-poppins text-sm text-[#0F1011]">Set as primary location</span>
                        </div>

                        <div className="flex gap-5 pt-4">
                            <button
                                type="submit"
                                disabled={!isFormValid || isCreating}
                                className={`flex-1 py-3 rounded-md text-white ${!isFormValid || isCreating
                                        ? 'bg-gray-400 cursor-not-allowed'
                                        : 'bg-[#002FD4] cursor-pointer'
                                    }`}
                            >
                                {isCreating ? 'Saving...' : 'Save Location'}
                            </button>
                            <button
                                type="button"
                                onClick={onClose}
                                className="flex-1 py-3 border rounded-md"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    )
}

export default AddLocationDialog