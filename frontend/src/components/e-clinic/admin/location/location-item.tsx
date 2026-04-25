// location-item.tsx
import { EnvelopeSimpleIcon, MapPinIcon, PencilIcon, PhoneIcon, TrashIcon } from "@phosphor-icons/react";

interface Location {
    title: string;
    address: string;
    phone: string;
    email: string;
    branch: string
}

export const LocationItem: React.FC<{
    location: Location;
    onEdit?: () => void;
    onDelete?: () => void;
}> = ({ location, onEdit, onDelete }) => {
    return (
        <div className="flex flex-col justify-between bg-white rounded-lg p-6 max-w-[416px] min-h-[283px] shadow-[6px_7px_20px_0px_#0000001A]">
            <div className="flex items-center mb-4">
                <div className="bg-[#E8EEFD] rounded-full w-[50px] h-[50px] flex items-center justify-center">
                    <MapPinIcon size={24} color="#002FD4" />
                </div>
                <div className="ml-2">
                    <div className="font-poppins font-medium text-base tracking-[-0.45px] align-middle text-[#0F1011]">
                        {location.title}
                    </div>
                    <div className="font-poppins font-semibold text-xs leading-4 tracking-normal align-middle text-[#002FD4]">
                        {location.branch} Branch
                    </div>
                </div>
            </div>

            <div className="mt-8 space-y-3 text-sm text-[#0F1011] font-poppins">
                {/* Address */}
                <div className="flex items-center gap-2">
                    <MapPinIcon className="w-5 h-5 text-[#002FD4] flex-shrink-0" />
                    <p className="font-normal leading-5 tracking-normal">
                        {location.address}
                    </p>
                </div>

                {/* Phone */}
                <div className="flex items-center gap-2">
                    <PhoneIcon className="w-5 h-5 text-[#002FD4] flex-shrink-0" />
                    <p className="font-normal leading-5 tracking-normal">
                        {location.phone}
                    </p>
                </div>

                {/* Email */}
                <div className="flex items-center gap-2">
                    <EnvelopeSimpleIcon className="w-5 h-5 text-[#002FD4] flex-shrink-0" />
                    <p className="font-normal leading-5 tracking-normal">
                        {location.email}
                    </p>
                </div>
            </div>

            <div className="mt-8 flex gap-5">
                <button
                    onClick={onEdit}
                    className="border border-[#002FD4] text-[#002FD4] flex-1 hover:cursor-pointer font-medium py-2.5 px-3 rounded-md transition duration-200 flex items-center justify-center gap-2"
                >
                    <PencilIcon />
                    <span className="font-semibold text-sm leading-5 tracking-normal text-center align-middle text-[#002FD4]">
                    Edit
                    </span>
                </button>

                <button
                    onClick={onDelete}
                    className="border border-[#002FD4] text-[#002FD4] flex-1 hover:cursor-pointer font-medium py-2.5 px-3 rounded-md transition duration-200 flex items-center justify-center gap-2"
                >
                    <TrashIcon />
                    <span className="font-semibold text-sm leading-5 tracking-normal text-center align-middle text-[#002FD4]">
                    Delete
                    </span>
                </button>
            </div>
        </div>
    );
};
