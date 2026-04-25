import { useEffect, useState } from "react";
import { X } from "@phosphor-icons/react";
import {
  useGetCommissionByService,
  useUpsertCommission,
} from "@/hooks/use-admin-comission-rate";
import { useServices } from "@/hooks/use-admin-service-hooks";

type Props = {
  open: boolean;
  mode: "create" | "edit";
  serviceId: string | null;
  onClose: () => void;
};

export default function EditCommissionModal({
  open,
  mode,
  serviceId,
  onClose,
}: Props) {
  const isEdit = mode === "edit";

  // EDIT → fetch fresh commission
  const { data: commission, isLoading } = useGetCommissionByService(
    serviceId,
    isEdit,
  );

  // CREATE → fetch services
  const { data: services = [] } = useServices({ enabled: !isEdit });

  const { mutate } = useUpsertCommission();

  const [selectedServiceId, setSelectedServiceId] = useState("");
  const [rate, setRate] = useState<number>(0);
  const [status, setStatus] = useState<"ACTIVE" | "INACTIVE">("ACTIVE");

  const handleRateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;

    // allow empty input while typing
    if (val === "") {
      setRate(0);
      return;
    }

    const num = Number(val);
    if (!isNaN(num)) {
      setRate(num);
    }
  };

  const handleRateBlur = () => {
    // force 2 decimals when user leaves input
    setRate((prev) => Number(prev.toFixed(2)));
  };

  useEffect(() => {
    if (commission && isEdit) {
      setRate(commission.rate);
      setStatus(commission.status);
    } else {
      setSelectedServiceId("");
      setRate(0);
      setStatus("ACTIVE");
    }
  }, [commission, isEdit]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white w-[460px] rounded-xl shadow-xl p-6">
        {/* Header */}
        <div className="flex justify-between mb-6">
          <h3 className="font-semibold text-lg">
            {isEdit ? "Edit Commission" : "Add Commission"}
          </h3>
          <button onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {isEdit && isLoading ? (
          <div className="py-10 text-center text-gray-400">
            Loading commission…
          </div>
        ) : (
          <>
            {/* CREATE ONLY */}
            {!isEdit && (
              <div className="mb-4">
                <label className="text-sm font-medium">Service</label>
                <select
                  value={selectedServiceId}
                  onChange={(e) => setSelectedServiceId(e.target.value)}
                  className="w-full mt-1 border px-3 py-2 rounded"
                >
                  <option value="">Select service</option>
                  {services.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.serviceName}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* RATE (BOTH) */}
            <div className="mb-4">
              <label className="text-sm font-medium">Rate (%)</label>
              <input
                type="number"
                step={0.5}
                min={0}
                value={rate.toFixed(2)}
                onChange={handleRateChange}
                onBlur={handleRateBlur}
                className="w-full mt-1 border px-3 py-2 rounded"
              />
            </div>

            {/* STATUS (EDIT ONLY) */}
            {isEdit && (
              <div className="mb-4">
                <label className="text-sm font-medium">Status</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as any)}
                  className="w-full mt-1 border px-3 py-2 rounded"
                >
                  <option value="ACTIVE">Active</option>
                  <option value="INACTIVE">Inactive</option>
                </select>
              </div>
            )}

            {/* Footer */}
            <div className="flex justify-end gap-3 mt-6">
              <button onClick={onClose} className="border px-4 py-2 rounded">
                Cancel
              </button>

              <button
                disabled={!isEdit && !selectedServiceId}
                onClick={() =>
                  mutate(
                    {
                      serviceId: isEdit ? serviceId! : selectedServiceId,
                      rate,
                      ...(isEdit && { status }),
                    },
                    { onSuccess: onClose },
                  )
                }
                className="bg-[#002FD4] text-white px-4 py-2 rounded disabled:opacity-50"
              >
                {isEdit ? "Update" : "Create"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
