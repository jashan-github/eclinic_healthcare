import {
  CurrencyDollar,
  MagnifyingGlassIcon,
  X,
  CaretDown,
} from "@phosphor-icons/react";
import { type FC, useState, useMemo } from "react";
import { Funnel, Globe, Tag, Check } from "@phosphor-icons/react";
import { WebinarItem } from "./webinar-item";
import {
  useAdminWebinars,
  useDeleteAdminWebinar,
} from "@/hooks/use-admin-webinars";
import { toast } from "react-toastify";
import { format, parseISO } from "date-fns";
import EditWebinarDialog from "./edit-webinar-dialog";
import ConfirmationModal from "@/components/ui/confirmation-modal";
import AgoraWebinarRoom from "@/components/e-clinic/doctor/webinars/agora-webinar-room";
import { useAuth } from "@/context/auth/auth-context-utils";

const WebinarsCard: FC = () => {
  const { data: webinarsData, isLoading, error } = useAdminWebinars();
  const { mutate: deleteWebinar, isPending: isDeleting } =
    useDeleteAdminWebinar();
  const { user } = useAuth();
  const [editingWebinar, setEditingWebinar] = useState<any | null>(null);
  const [deletingWebinar, setDeletingWebinar] = useState<{
    id: string;
    title: string;
  } | null>(null);
  const [activeWebinar, setActiveWebinar] = useState<{ id: string } | null>(
    null,
  );

  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<"all" | "free" | "paid">("all");
  const [showDropdown, setShowDropdown] = useState(false);

  const handleDeleteWebinar = (id: string, title: string) => {
    setDeletingWebinar({ id, title });
  };

  const confirmDelete = () => {
    if (!deletingWebinar) return;

    deleteWebinar(deletingWebinar.id, {
      onSuccess: () => {
        toast.success("Webinar deleted successfully!");
        setDeletingWebinar(null);
      },
      onError: (error: any) => {
        toast.error(error?.message || "Failed to delete webinar");
        setDeletingWebinar(null);
      },
    });
  };

  const handleGoLive = (webinarId: string) => {
    setActiveWebinar({ id: webinarId });
  };

  const handleLeaveWebinar = () => {
    setActiveWebinar(null);
  };

  // Transform API data to match WebinarItem props
  const transformedWebinars = useMemo(() => {
    if (!webinarsData?.data?.webinars) return [];

    return webinarsData.data.webinars.map((webinar) => {
      // Calculate duration from start_time and end_time
      const [startHours, startMinutes] = webinar.start_time.split(":");
      const startTotalMinutes =
        parseInt(startHours) * 60 + parseInt(startMinutes);
      const [endHours, endMinutes] = webinar.end_time.split(":");
      const endTotalMinutes = parseInt(endHours) * 60 + parseInt(endMinutes);
      const durationMinutes = endTotalMinutes - startTotalMinutes;

      // Format time for display
      const hour = parseInt(startHours);
      const ampm = hour >= 12 ? "PM" : "AM";
      const hour12 = hour % 12 || 12;
      const displayTime = `${String(hour12).padStart(2, "0")}:${startMinutes} ${ampm}`;

      return {
        id: webinar.id,
        doctorName: webinar.host.name || "Healthcare Provider", // Replace with actual host name when available
        specialty: "", // Replace with actual specialty when available
        title: webinar.title,
        date: format(parseISO(webinar.webinar_date), "dd MMM yyyy"),
        time: displayTime,
        duration: `${durationMinutes} mins`,
        seats: `${webinar.registered_count} / ${webinar.participant_limit} filled`,
        currency: webinar.currency,
        price: webinar.price,
        type: webinar.pricing_type,
        imageUrl: webinar.host.profile_image,
        status: webinar.status,
        originalData: webinar, // Store original data for editing
        onEdit: () => setEditingWebinar(webinar),
        onDelete: () => handleDeleteWebinar(webinar.id, webinar.title),
        onGoLive: () => handleGoLive(webinar.id),
      };
    });
  }, [webinarsData]);

  const filteredWebinars = useMemo(() => {
    return transformedWebinars.filter((webinar) => {
      const matchesSearch = webinar.title
        .toLowerCase()
        .includes(searchQuery.toLowerCase());

      const matchesFilter = filterType === "all" || webinar.type === filterType;

      return matchesSearch && matchesFilter;
    });
  }, [transformedWebinars, searchQuery, filterType]);

  if (activeWebinar) {
    return (
      <AgoraWebinarRoom
        webinarId={activeWebinar.id}
        isHost={true}
        userRole="admin"
        userName={user?.name || "Admin"}
        onLeave={handleLeaveWebinar}
      />
    );
  }

  if (isLoading) {
    return (
      <div className="py-10 px-2">
        <div className="text-center py-20 text-gray-500 font-poppins">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#002FD4] mx-auto"></div>
          <p className="mt-4">Loading webinars...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-10 px-2">
        <div className="text-center py-20 text-red-500 font-poppins">
          Failed to load webinars. Please try again.
        </div>
      </div>
    );
  }

  return (
    <div className="py-10 px-2">
      <h2 className="font-poppins font-semibold text-2xl text-[#0F1011] mb-8">
        All Webinars
      </h2>

      <div className="mb-10 flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <MagnifyingGlassIcon
            color="black"
            size={20}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
          />
          <input
            type="text"
            placeholder="Search by Name"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="font-poppins w-full pl-12 pr-10 py-2 rounded-md border border-[#DADEE3] focus:outline-none focus:border-[#002FD4] transition-colors font-poppins bg-white"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="hover:cursor-pointer absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X size={20} color="black" />
            </button>
          )}
        </div>

        <div className="relative">
          <div
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center gap-2 bg-white w-[150px] h-[39px] px-3 rounded-md border border-[#DADEE3] hover:border-gray-300 transition-all cursor-pointer select-none"
          >
            <Funnel size={16} weight="bold" className="text-[#0F172A]" />

            <span className="flex-1 font-poppins font-bold text-[13px] leading-4 text-black text-center">
              {filterType === "all" && "All"}
              {filterType === "free" && "Free"}
              {filterType === "paid" && "Paid"}
            </span>

            <CaretDown
              size={14}
              weight="bold"
              className={`text-[#0F1011] transition-transform ${showDropdown ? "rotate-180" : ""}`}
            />
          </div>

          {showDropdown && (
            <div className="absolute top-full left-0 mt-1 w-[150px] bg-white rounded-md shadow-lg border border-gray-200 overflow-hidden z-50">
              {(["all", "free", "paid"] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => {
                    setFilterType(type);
                    setShowDropdown(false);
                  }}
                  className="w-full px-4 py-2.5 text-left flex items-center justify-between hover:bg-gray-50 transition-colors font-poppins text-sm font-medium text-[#0F172A]"
                >
                  <span className="flex items-center gap-2">
                    {type === "all" && <Globe size={15} />}
                    {type === "free" && (
                      <Tag size={15} className="text-green-600" />
                    )}
                    {type === "paid" && <CurrencyDollar size={15} />}
                    {type === "all" ? "All" : type === "free" ? "Free" : "Paid"}
                  </span>
                  {filterType === type && (
                    <Check size={15} weight="bold" className="text-[#002FD4]" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {filteredWebinars.length === 0 ? (
        <div className="text-center py-20 text-gray-500 font-poppins">
          No webinars found matching your search.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
          {filteredWebinars.map((webinar) => (
            <WebinarItem key={webinar.id} {...webinar} />
          ))}
        </div>
      )}

      {/* Edit Webinar Dialog */}
      <EditWebinarDialog
        isOpen={!!editingWebinar}
        onClose={() => setEditingWebinar(null)}
        webinar={editingWebinar}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={!!deletingWebinar}
        onClose={() => setDeletingWebinar(null)}
        onConfirm={confirmDelete}
        title="Delete Webinar"
        message={`Are you sure you want to delete "${deletingWebinar?.title}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        confirmButtonColor="danger"
        isLoading={isDeleting}
      />
    </div>
  );
};

export default WebinarsCard;
