import { Modal, TextInput, Loader } from "@mantine/core";
import { MagnifyingGlassIcon, UserIcon } from "@phosphor-icons/react";
import { useEffect, useRef } from "react";
import { usePatients } from "@/features/app/patients/hooks/use-patients";
import { useChatService } from "../patients/hooks/use-chat-service";

interface StartNewChatModalProps {
  opened: boolean;
  onClose: () => void;
  onSelectPatient: (patientId: string) => void;
}

export const StartNewChatModal: React.FC<StartNewChatModalProps> = ({
  opened,
  onClose,
  onSelectPatient,
}) => {
  const { patients, isLoading, isFetching, page, setPage, totalPages } =
    usePatients();
  const createChatMutation = useChatService().createChat;

  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!loadMoreRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !isFetching && page < totalPages) {
          setPage((p) => p + 1);
        }
      },
      { threshold: 1 },
    );

    observer.observe(loadMoreRef.current);
    return () => observer.disconnect();
  }, [isFetching, page, setPage, totalPages]);

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Start New Chat"
      size="md"
      centered
    >
      <TextInput
        placeholder="Search patients..."
        leftSection={<MagnifyingGlassIcon size={16} />}
        mb="md"
        className="mt-2"
      />

      <div className="max-h-[400px] overflow-y-auto">
        {isLoading ? (
          <div className="flex justify-center py-6">
            <Loader size="sm" />
          </div>
        ) : (
          patients.map((patient) => (
            <div
              key={patient.id}
              onClick={() => {
                createChatMutation(patient.id);
                onSelectPatient(patient.id);
                onClose();
              }}
              className="flex items-center gap-3 p-3 rounded-md cursor-pointer hover:bg-gray-100"
            >
              <div className="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center">
                <UserIcon size={18} />
              </div>

              <div>
                <p className="font-medium">{patient.name}</p>
                <p className="text-sm text-gray-500">{patient.email}</p>
              </div>
            </div>
          ))
        )}

        {/* Infinite scroll trigger */}
        <div ref={loadMoreRef} className="py-4 text-center">
          {isFetching && <Loader size="xs" />}
        </div>
      </div>
    </Modal>
  );
};
