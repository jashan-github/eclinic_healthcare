// src/components/e-clinic/admin/vitals/vitals-table.tsx
import { MagnifyingGlassIcon, X, PencilSimple, Trash } from "@phosphor-icons/react"
import { useMemo, useState } from "react"
import AddVitalDialog from "./add-vital-dialog"
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core"
import {
  arrayMove,
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable"
import { useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { Loader } from '@mantine/core'
import ConfirmationModal from '@/components/ui/confirmation-modal'
import { useDeleteVital, useReorderVitals, useVitals } from "@/pages/app/settings/hooks/use-admin-vitals"

// Sortable Row - Entire row draggable
function SortableVitalRow({ vital, index }: { vital: any; index: number }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: vital.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <tr
      ref={setNodeRef}
      style={style}
      className={`hover:bg-[#F4F6F9] transition-all ${isDragging ? 'opacity-70 shadow-2xl z-50' : ''}`}
    >
      {/* Poori row ko drag handle bana rahe hain, lekin actions cell ko exclude */}
      <td
        {...attributes}
        {...listeners}
        className="py-4 px-4 cursor-grab active:cursor-grabbing"
      >
        {index + 1}
      </td>
      <td
        {...attributes}
        {...listeners}
        className="py-4 px-4 font-medium cursor-grab active:cursor-grabbing"
      >
        {vital.name}
      </td>
      <td
        {...attributes}
        {...listeners}
        className="py-4 px-4 cursor-grab active:cursor-grabbing"
      >
        {vital.unit}
      </td>
      <td
        {...attributes}
        {...listeners}
        className="py-4 px-4 cursor-grab active:cursor-grabbing"
      >
        {vital.data_type}
      </td>
      <td
        {...attributes}
        {...listeners}
        className="py-4 px-4 cursor-grab active:cursor-grabbing"
      >
        <span className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${
          vital.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
        }`}>
          {vital.is_active ? 'Active' : 'Inactive'}
        </span>
      </td>
      {/* Actions cell - drag handle nahi lagaya */}
      <td className="py-4 px-4">
        <div className="flex items-center gap-3 justify-center">
          <button
            onClick={(e) => {
              e.stopPropagation(); // ← Critical: drag prevent on button click
              handleEdit(vital.id);
            }}
            className="p-2 rounded-full hover:bg-[#F4F6F9] transition-colors"
            title="Edit Vital"
          >
            <PencilSimple size={16} weight="regular" className="text-gray-600" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDeleteClick(vital.id, vital.name);
            }}
            className="p-2 rounded-full hover:bg-red-50 transition-colors"
            title="Delete Vital"
          >
            <Trash size={16} weight="regular" className="text-gray-600 hover:text-red-600" />
          </button>
        </div>
      </td>
    </tr>
  )
}

let handleEdit: (id: string) => void
let handleDeleteClick: (id: string, name: string) => void

export default function VitalsTable() {
  const [searchTerm, setSearchTerm] = useState('')
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [selectedVitalId, setSelectedVitalId] = useState<string | null>(null)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [vitalToDelete, setVitalToDelete] = useState<string | null>(null)
  const [vitalToDeleteName, setVitalToDeleteName] = useState<string>("")

  const { data: vitals = [], isLoading } = useVitals()
  const reorderMutation = useReorderVitals()
  const deleteVitalMutation = useDeleteVital()

  const filteredVitals = useMemo(() => {
    return vitals.filter(vital =>
      vital.name.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [vitals, searchTerm])

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor)
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id) return

    const oldIndex = vitals.findIndex((i) => i.id === active.id)
    const newIndex = vitals.findIndex((i) => i.id === over.id)
    const newOrder = arrayMove(vitals, oldIndex, newIndex)

    reorderMutation.mutate(newOrder)
  }

  handleEdit = (id: string) => {
    setSelectedVitalId(id)
    setIsEditModalOpen(true)
  }

  handleDeleteClick = (id: string, name: string) => {
    setVitalToDelete(id)
    setVitalToDeleteName(name)
    setIsDeleteModalOpen(true)
  }

  const handleConfirmDelete = () => {
    if (vitalToDelete) {
      deleteVitalMutation.mutate(vitalToDelete, {
        onSuccess: () => {
          setIsDeleteModalOpen(false)
          setVitalToDelete(null)
          setVitalToDeleteName("")
        }
      })
    }
  }

  const handleCancelDelete = () => {
    setIsDeleteModalOpen(false)
    setVitalToDelete(null)
    setVitalToDeleteName("")
  }

  const handleCloseModal = () => {
    setIsEditModalOpen(false)
    setSelectedVitalId(null)
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-64"><Loader /></div>
  }

  return (
    <>
      <div className="w-full mt-4">
        {/* Search Bar */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6 items-center">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search by Vital Name"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={`w-full pl-10 ${searchTerm ? 'pr-10' : 'pr-4'} py-2 border border-gray-300 rounded-md 
                focus:outline-none focus:ring-2 focus:ring-[#002FD4]
                font-poppins font-normal text-[14px] leading-[100%] 
                text-black placeholder:text-[#A5ABB3]`}
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-[#F4F6F9] rounded-md transition-colors"
              >
                <X size={16} weight="bold" className="text-gray-400 hover:text-gray-600" />
              </button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <div className="min-w-[900px] border border-[#E4E5ED] rounded-lg overflow-hidden">
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <table className="w-full table-auto border-collapse">
                <thead className="bg-[#E8EEFD]">
                  <tr>
                    <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">Sr. No.</th>
                    <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">Vital Name</th>
                    <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">Unit</th>
                    <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">Data Type</th>
                    <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">Status</th>
                    <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-[#E4E5ED] font-poppins font-normal text-[13px] leading-[20px] text-[#0F1011]">
                  <SortableContext items={filteredVitals} strategy={verticalListSortingStrategy}>
                    {filteredVitals.map((vital, index) => (
                      <SortableVitalRow key={vital.id} vital={vital} index={index} />
                    ))}
                  </SortableContext>
                </tbody>
              </table>
            </DndContext>
          </div>
        </div>
      </div>

      <AddVitalDialog
        isOpen={isEditModalOpen}
        onClose={handleCloseModal}
        vitalId={selectedVitalId}
      />
      <ConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Delete Vital"
        message={`Are you sure you want to delete "${vitalToDeleteName}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        confirmButtonColor="danger"
        isLoading={deleteVitalMutation.isPending}
      />
    </>
  )
}