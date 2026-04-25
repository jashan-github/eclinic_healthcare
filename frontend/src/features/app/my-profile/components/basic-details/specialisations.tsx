// import ErrorWhileFetchingData from '@/components/orvo/common/ErrorWhileFetchingData'
// import GlobalLoader from '@/components/orvo/common/GlobalLoader'
// import { Badge } from '@/components/ui/badge'
// import { Button } from '@/components/ui/button'
// import {
//   Select,
//   SelectContent,
//   SelectItem,
//   SelectTrigger,
//   SelectValue
// } from '@/components/ui/select'
// import { useSpecializations } from '@/features/App/MyProfile/hooks/useSpecializations'
// import { predefinedSpecializations } from '@/lib/specializations'

// import type { Specialization } from '@/types/Specialization'
// import { Pencil, Star, Trash } from 'lucide-react'
// import { useEffect, useState, type FC, type ReactElement } from 'react'

// const Specializations: FC = (): ReactElement => {
//   const {
//     specializations: fetchedSpecializations,
//     isLoading,
//     error,
//     saveSpecialization,
//     deleteSpecialization
//   } = useSpecializations()

//   const [specializations, setSpecializations] = useState<Specialization[]>([])
//   const [specialization, setSpecialization] = useState<string>('')

//   // Sync local state with fetched specializations
//   useEffect(() => {
//     if (fetchedSpecializations) {
//       const mappedSpecializations = fetchedSpecializations.map(
//         (fetchedSpecialization: Specialization) => {
//           const spec = predefinedSpecializations.find(
//             (pS) => pS.value === value
//           ) || { label: value, value }
//           return { ...spec, major: false } // Assume major is not fetched; adjust if API provides it
//         }
//       )
//       setSpecializations(mappedSpecializations)
//     }
//   }, [fetchedSpecializations])

//   // Add a new specialization to the list
//   const addSpecializationToList = (value: string) => {
//     const spec = predefinedSpecializations.find((pS) => pS.value === value)
//     if (!spec) return // Prevent adding invalid specializations

//     const newSpecialization = {
//       label: spec.label,
//       value: spec.value,
//       major: false
//     }
//     setSpecializations((prev) => [...prev, newSpecialization])
//     setSpecialization('') // Reset dropdown
//   }

//   // Toggle major status for a specialization
//   const toggleMajor = (value: string) => {
//     setSpecializations((prev) =>
//       prev.map((spec) =>
//         spec.value === value ? { ...spec, major: !spec.major } : spec
//       )
//     )
//   }

//   // Remove a specialization
//   const removeSpecialization = (value: string) => {
//     setSpecializations((prev) => prev.filter((spec) => spec.value !== value))
//     deleteSpecialization(value) // Call API to delete
//   }

//   // Save specializations to backend
//   const onSubmit = () => {
//     const services = specializations.map((spec) => spec.value)
//     saveSpecialization({ specialization: '', services }) // Save to API
//   }

//   if (isLoading) return <GlobalLoader />
//   if (error) return <ErrorWhileFetchingData />

//   return (
//     <div className="py-4 flex flex-col gap-4">
//       {/* Available Specializations selected */}
//       <Select
//         onValueChange={addSpecializationToList}
//         value={specialization}
//       >
//         <SelectTrigger className="w-full orvo-base-input">
//           <SelectValue placeholder="Select specialisation" />
//         </SelectTrigger>
//         <SelectContent className="border-gray-200">
//           {predefinedSpecializations &&
//             predefinedSpecializations.map(({ label, value }) => (
//               <SelectItem
//                 key={value}
//                 value={value}
//               >
//                 {label}
//               </SelectItem>
//             ))}
//         </SelectContent>
//       </Select>

//       {/* Specializations selected by Doctor */}
//       {specializations &&
//         specializations.map(({ label, major }) => (
//           <div className="flex items-center justify-between gap-2 border border-gray-300 p-2 rounded ">
//             <div className="">
//               <Button
//                 variant={'ghost'}
//                 size={'icon'}
//               >
//                 <Star size={16} />
//               </Button>
//             </div>
//             <div className="grow flex gap-2">
//               <div className="">{label}</div>
//               {major && <Badge className="bg-gray-400">Major</Badge>}
//             </div>
//             <div className="flex gap-2">
//               <Button
//                 variant={'ghost'}
//                 size={'icon'}
//               >
//                 <Pencil size={16} />
//               </Button>
//               <Button
//                 variant={'ghost'}
//                 size={'icon'}
//               >
//                 <Trash size={16} />
//               </Button>
//             </div>
//           </div>
//         ))}

//       {/* Save/Update Button */}
//       <Button type="submit">Done</Button>
//     </div>
//   )
// }

// export default Specializations

const Specialisations = () => {
  return <div>Specialisations</div>
}

export default Specialisations
