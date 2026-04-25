// weekly-schedule-item-slot.tsx

import BaseTimePicker from "@/components/form/BaseTimePicker";
import type {
  DoctorSchedule,
  DoctorScheduleAppointmentService,
} from "@/types/calendar";
import {
  ActionIcon,
  Card,
  Select,
  Radio,
  Button,
  Stack,
  Text,
  Group,
  Input,
} from "@mantine/core";
import {
  MagnifyingGlassIcon,
  MinusIcon,
  PlusIcon,
  XIcon,
  PencilIcon,
} from "@phosphor-icons/react";
import {
  useState,
  useEffect,
  forwardRef,
  useImperativeHandle,
  type ReactElement,
} from "react";
import { toast } from "react-toastify";
import BaseSideSheet from "@/components/orvo/base-side-sheet";
import { useCalendarService } from "../../../hooks/use-calendar-service-doctor";
import {
  useUpdateWeeklySchedule,
  useCreateDoctorAvailability,
  useUpdateDoctorAvailability,
  useAddDoctorService,
  useAssignServiceToAvailability,
  useAvailabilityServices,
  useUpdateAvailabilityService,
  useDeleteAvailabilityService,
  useDeleteDoctorService,
  useGetDoctorServices,
  useAvailabilityServicePricing,
  useDoctorServicePricing,
  useCreateAvailabilityServicePricing,
  useUpdateAvailabilityServicePricing,
  useDeleteAvailabilityServicePricing,
  useCreateDoctorServicePricing,
  useDeleteDoctorServicePricing,
} from "@/hooks/use-weekly-schedule";
import type { WeeklySchedulePayload } from "@/services/weekly-schedule";
import {
  buildCreateAvailabilityPayload,
  buildUpdateAvailabilityPayload,
  getAvailabilityServicePricing,
  getDoctorServicePricing,
} from "@/services/weekly-schedule";
import { useAuth } from "@/context/auth/auth-context-utils";

interface WeeklyScheduleItemSlotProps {
  initialData: DoctorSchedule;
  showDeleteButton?: boolean;
  onDelete?: (slotId: string) => void;
  onCopy?: () => void;
  onAddNewSlot: () => void;
  onScheduleUpdated?: () => void;
  onServiceAdded?: () => void;
}

export interface WeeklyScheduleItemSlotHandle {
  saveAvailability: () => Promise<void>;
}

const WeeklyScheduleItemSlot = forwardRef<
  WeeklyScheduleItemSlotHandle,
  WeeklyScheduleItemSlotProps
>(
  (
    {
      initialData,
      showDeleteButton = false,
      onDelete,
      onAddNewSlot,
      onScheduleUpdated,
      // onServiceAdded: _onServiceAdded
    },
    ref,
  ): ReactElement => {
    const { calendarServicesFormatted, calendarServices } =
      useCalendarService();
    const { user } = useAuth();

    const [startTime, setStartTime] = useState<string | null>(
      initialData.start_time ?? "",
    );
    const [endTime, setEndTime] = useState<string | null>(
      initialData.end_time ?? "",
    );
    const [services, setServices] = useState<
      DoctorScheduleAppointmentService[]
    >(initialData.appointment_services ?? []);
    const [isSaved, setIsSaved] = useState<boolean>(
      !initialData.draft && !!initialData.id,
    );
    const [editingService, setEditingService] =
      useState<DoctorScheduleAppointmentService | null>(null);
    const [editConsultationMode, setEditConsultationMode] = useState<
      "IN_CLINIC" | "TELECONSULTATION"
    >("IN_CLINIC");
    const [editDuration, setEditDuration] = useState<number>(30);
    const [editPrice, setEditPrice] = useState<string>("");
    const [editPaymentMode, setEditPaymentMode] = useState<
      "prepaid" | "postpaid"
    >("prepaid");
    const [editNickname, setEditNickname] = useState<string>("");
    const [editAllowBooking, setEditAllowBooking] = useState<boolean>(true);
    const [editAdvanceBookingDays, setEditAdvanceBookingDays] =
      useState<number>(0);
    const [editMinimumNoticeHours, setEditMinimumNoticeHours] =
      useState<number>(0);
    const [editAppointmentType, setEditAppointmentType] = useState<
      "regular" | "followup"
    >("regular");
    const [editFollowupValidity, setEditFollowupValidity] =
      useState<string>("7");
    const [selectedServiceId, setSelectedServiceId] = useState<string | null>(
      null,
    );

    // Fetch availability pricing when editing a service
    const assignmentIdForPricing = editingService?.assignment_id;
    const { data: availabilityPricingResponse } = useAvailabilityServicePricing(
      assignmentIdForPricing || undefined,
    );

    // Fetch service pricing (for fallback)
    const serviceIdForPricing = editingService?.id;
    const { data: servicePricingResponse } = useDoctorServicePricing(
      serviceIdForPricing || undefined,
      !!editingService,
    );

    // Extract availability pricing data
    const availabilityPricingData =
      availabilityPricingResponse?.data &&
      availabilityPricingResponse.data.length > 0
        ? availabilityPricingResponse.data[0]
        : null;

    // Extract service pricing data
    const servicePricingData =
      servicePricingResponse?.data && servicePricingResponse.data.length > 0
        ? servicePricingResponse.data[0]
        : null;

    const updateScheduleMutation = useUpdateWeeklySchedule();
    const createAvailabilityMutation = useCreateDoctorAvailability();
    const updateAvailabilityMutation = useUpdateDoctorAvailability();
    const addDoctorServiceMutation = useAddDoctorService();
    const assignServiceToAvailabilityMutation =
      useAssignServiceToAvailability();
    const updateAvailabilityServiceMutation = useUpdateAvailabilityService();
    const deleteAvailabilityServiceMutation = useDeleteAvailabilityService();
    const deleteDoctorServiceMutation = useDeleteDoctorService();
    const createAvailabilityServicePricingMutation =
      useCreateAvailabilityServicePricing();
    const updateAvailabilityServicePricingMutation =
      useUpdateAvailabilityServicePricing();
    const deleteAvailabilityServicePricingMutation =
      useDeleteAvailabilityServicePricing();
    const createDoctorServicePricingMutation = useCreateDoctorServicePricing();
    const deleteDoctorServicePricingMutation = useDeleteDoctorServicePricing();

    // Fetch availability services from API
    const { data: availabilityServices = [], isLoading: isLoadingServices } =
      useAvailabilityServices(
        initialData.id && !initialData.draft ? initialData.id : undefined,
      );

    // Fetch doctor services to get doctor_service_id (primary key)
    const { data: doctorServices = [] } = useGetDoctorServices();

    // Check if this is a draft (new) slot
    const isDraft = initialData.draft || !initialData.id;

    // Update isSaved when initialData changes (e.g., after creation)
    useEffect(() => {
      setIsSaved(!initialData.draft && !!initialData.id);
    }, [initialData.draft, initialData.id]);

    // Update services when availability services are fetched from API
    useEffect(() => {
      // Prevent infinite loop by checking if services actually changed
      if (availabilityServices.length > 0 && !isDraft && !isLoadingServices) {
        console.log("=== Mapping availabilityServices to local services ===");
        console.log(
          "availabilityServices from API:",
          JSON.stringify(availabilityServices, null, 2),
        );

        const mappedServices: DoctorScheduleAppointmentService[] =
          availabilityServices.map((availService) => {
            // Find matching doctor service by service_id to get the primary key id
            const doctorService = doctorServices.find(
              (ds) => ds.service_id === availService.service_id,
            );

            console.log("Mapping service:", {
              service_id: availService.service_id,
              service_name: availService.service_name,
              consultation_mode: availService.consultation_mode,
              consultation_mode_type: typeof availService.consultation_mode,
            });

            return {
              id: availService.service_id,
              service_name: availService.service_name || "Unknown Service",
              amount: 0, // Price not in response, will need to fetch separately if needed
              duration: availService.slot_duration_minutes || 30,
              payment_mode: "prepaid" as const,
              consultation_mode: availService.consultation_mode,
              assignment_id: availService.id, // Primary key id from availability-services
              doctor_service_id: doctorService?.id, // Primary key id from doctor-services
            };
          });

        console.log(
          "Mapped services:",
          JSON.stringify(mappedServices, null, 2),
        );

        // Check if services actually changed by comparing full objects, not just IDs
        const servicesChanged =
          JSON.stringify(services) !== JSON.stringify(mappedServices);

        if (servicesChanged) {
          console.log("Services changed, updating state");
          setServices(mappedServices);
        } else {
          console.log("Services unchanged, skipping update");
        }
      } else if (
        availabilityServices.length === 0 &&
        !isDraft &&
        !isLoadingServices &&
        services.length > 0
      ) {
        // If no services found and not loading, clear services only if we have services
        console.log("No availability services found, clearing local services");
        setServices([]);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [availabilityServices, doctorServices, isDraft, isLoadingServices]);

    // Handle time changes - update local state and trigger API update for existing slots
    const handleTimeChange = (
      newStartTime: string | null,
      newEndTime: string | null,
    ) => {
      setStartTime(newStartTime);
      setEndTime(newEndTime);

      // If it's an existing slot (not draft) and times are valid, update via PUT endpoint
      if (
        !isDraft &&
        initialData.id &&
        newStartTime &&
        newEndTime &&
        user?.id
      ) {
        // Check if times actually changed from initial values
        if (
          newStartTime !== initialData.start_time ||
          newEndTime !== initialData.end_time
        ) {
          const payload = buildUpdateAvailabilityPayload(
            initialData.day_name,
            newStartTime,
            newEndTime,
            user.clinic_id,
          );

          updateAvailabilityMutation.mutate(
            { availabilityId: initialData.id, payload },
            {
              onSuccess: () => {
                onScheduleUpdated?.();
              },
              onError: () => {
                // Revert to original times on error
                setStartTime(initialData.start_time);
                setEndTime(initialData.end_time);
                toast.error("Failed to update time slot");
              },
            },
          );
        }
      }
    };

    // Expose save function to parent component
    const saveAvailability = (): Promise<void> => {
      return new Promise((resolve, reject) => {
        if (!startTime || !endTime) {
          toast.error("Please set both start and end times");
          reject(new Error("Times not set"));
          return;
        }

        if (isDraft && user?.id) {
          // Create new availability
          const payload = buildCreateAvailabilityPayload(
            initialData.day_name,
            startTime,
            endTime,
            user.clinic_id,
          );

          createAvailabilityMutation.mutate(
            { doctorId: user.id, payload },
            {
              onSuccess: () => {
                setIsSaved(true);
                toast.success("Availability saved! You can now add services.");
                onScheduleUpdated?.();
                resolve();
              },
              onError: (error) => {
                toast.error("Failed to save availability");
                reject(error);
              },
            },
          );
        } else if (!isDraft && initialData.id && user?.id) {
          // Update existing availability using PUT endpoint
          const payload = buildUpdateAvailabilityPayload(
            initialData.day_name,
            startTime,
            endTime,
            user.clinic_id,
          );

          updateAvailabilityMutation.mutate(
            { availabilityId: initialData.id, payload },
            {
              onSuccess: () => {
                toast.success("Availability updated successfully!");
                onScheduleUpdated?.();
                resolve();
              },
              onError: (error) => {
                toast.error("Failed to update availability");
                reject(error);
              },
            },
          );
        } else {
          reject(new Error("User ID not available"));
        }
      });
    };

    // Expose saveAvailability to parent via ref
    useImperativeHandle(
      ref,
      () => ({
        saveAvailability,
      }),
      [startTime, endTime, isDraft, user?.id, services],
    );

    const buildPayload = (
      currentServices: DoctorScheduleAppointmentService[],
    ): WeeklySchedulePayload => ({
      weekdata: [
        {
          day_name: initialData.day_name,
          doctor_schedules: [
            {
              id: initialData.id || null,
              day_off: false,
              start_time: startTime || initialData.start_time || "09:00",
              end_time: endTime || initialData.end_time || "17:00",
              appointment_services: currentServices.map((s) => ({
                id: s.id,
                service_name: s.service_name,
              })),
            },
          ],
        },
      ],
    });

    const handleServiceSelect = (serviceId: string | null) => {
      if (!serviceId) {
        setSelectedServiceId(null);
        return;
      }

      if (services.some((s) => s.id === serviceId)) {
        toast.info("Service already added");
        return;
      }

      const selectedService = calendarServices.find((s) => s.id === serviceId);
      if (!selectedService) {
        return;
      }

      // Check if availability slot is saved (has ID)
      if (!initialData.id || isDraft) {
        toast.error(
          "Please save the availability slot first before adding services",
        );
        return;
      }

      setSelectedServiceId(serviceId);

      const slotDurationMinutes = selectedService.duration || 30;

      // Step 1: Add service to doctor's offerings
      addDoctorServiceMutation.mutate(
        {
          service_id: serviceId,
          slot_duration_minutes: slotDurationMinutes,
        },
        {
          onSuccess: (doctorServiceResponse) => {
            // Get doctor_service_id (primary key) from addDoctorService response
            const doctorServiceId =
              doctorServiceResponse?.data?.id ||
              (doctorServiceResponse as any)?.id ||
              undefined;

            // Step 2: Assign service to availability
            // Determine consultation mode from type field (which contains service_mode from API)
            // type can be 'IN_CLINIC', 'TELECONSULTATION', 'visit', or 'video'
            const consultationMode =
              selectedService.type === "IN_CLINIC" ||
              selectedService.type === "visit"
                ? "IN_CLINIC"
                : "TELECONSULTATION";

            assignServiceToAvailabilityMutation.mutate(
              {
                availability_id: initialData.id,
                consultation_mode: consultationMode,
                service_id: serviceId,
                slot_duration_minutes: slotDurationMinutes,
              },
              {
                onSuccess: (response) => {
                  // Update local state after both APIs succeed
                  // Determine payment mode from selected service
                  const paymentMethod = selectedService.payment_method || "";
                  const paymentMode: "prepaid" | "postpaid" =
                    paymentMethod.toLowerCase() === "prepaid" ||
                    paymentMethod.toLowerCase() === "pre_paid"
                      ? "prepaid"
                      : "postpaid";

                  // Determine consultation mode from type field (which contains service_mode from API)
                  const consultationMode: "IN_CLINIC" | "TELECONSULTATION" =
                    selectedService.type === "IN_CLINIC" ||
                    selectedService.type === "visit"
                      ? "IN_CLINIC"
                      : "TELECONSULTATION";

                  // Get assignment_id (primary key from availability-services) from response if available
                  const assignmentId =
                    response?.data?.id || (response as any)?.id || undefined;

                  const newService: DoctorScheduleAppointmentService = {
                    id: serviceId,
                    service_name:
                      selectedService.nickname || selectedService.service_name,
                    amount: selectedService.amount,
                    duration: selectedService.duration,
                    payment_mode: paymentMode,
                    consultation_mode: consultationMode,
                    assignment_id: assignmentId, // Primary key from availability-services
                    doctor_service_id: doctorServiceId, // Primary key from doctor-services
                  };

                  const updatedServices = [...services, newService];
                  setServices(updatedServices);
                  setSelectedServiceId(null); // Clear selection after successful add
                  toast.success("Service added successfully!");
                  onScheduleUpdated?.();
                },
                onError: (error) => {
                  toast.error(
                    error.message || "Failed to assign service to availability",
                  );
                  setSelectedServiceId(null);
                },
              },
            );
          },
          onError: (error) => {
            toast.error(
              error.message || "Failed to add service to doctor offerings",
            );
            setSelectedServiceId(null);
          },
        },
      );
    };

    const handleEditService = (service: DoctorScheduleAppointmentService) => {
      setEditingService(service);

      const consultationMode =
        service.consultation_mode === "TELECONSULTATION"
          ? "TELECONSULTATION"
          : "IN_CLINIC";
      console.log("Computed consultationMode:", consultationMode);
      console.log("Setting editConsultationMode to:", consultationMode);
      setEditConsultationMode(consultationMode);

      setEditDuration(
        typeof service.duration === "number"
          ? service.duration
          : parseInt(String(service.duration)) || 30,
      );
      setEditPaymentMode(service.payment_mode || "prepaid");
      setEditNickname(service.nickname || "");
      setEditAllowBooking(service.allow_patient_booking ?? true);
      setEditAdvanceBookingDays(service.advance_booking_days ?? 0);
      setEditMinimumNoticeHours(
        service.minimum_notice_minutes
          ? Math.floor(service.minimum_notice_minutes / 60)
          : 0,
      );
      setEditAppointmentType(
        service.appointment_type?.toLowerCase() === "followup"
          ? "followup"
          : "regular",
      );
      setEditFollowupValidity(
        service.follow_up_validity ? String(service.follow_up_validity) : "7",
      );
    };

    // Update consultation mode when editing service changes
    useEffect(() => {
      if (editingService) {
        const consultationMode =
          editingService.consultation_mode === "TELECONSULTATION"
            ? "TELECONSULTATION"
            : "IN_CLINIC";
        console.log(
          "useEffect: Updating consultation mode to:",
          consultationMode,
          "from editingService.consultation_mode:",
          editingService.consultation_mode,
        );
        setEditConsultationMode(consultationMode);
      }
    }, [editingService]);

    // Update form fields when pricing data is loaded
    // Priority: 1. availability price_amount, 2. service price_amount, 3. global_price
    useEffect(() => {
      if (editingService) {
        // Priority order:
        // 1. price_amount from availability-pricing
        // 2. price_amount from service-pricing (service amount)
        // 3. global_price as fallback
        const price =
          availabilityPricingData?.price_amount ??
          servicePricingData?.price_amount ??
          availabilityPricingData?.global_price ??
          null;

        if (price != null) {
          setEditPrice(String(price));
        } else {
          setEditPrice("0");
        }
      }
    }, [editingService, availabilityPricingData, servicePricingData]);
    console.log("editingService", editingService);

    const handleUpdateService = async () => {
      if (!editingService) {
        toast.error("Cannot update service: service not found");
        return;
      }

      console.log("editingService before update", editingService);
      console.log("availabilityServices", availabilityServices);

      // assignment_id is required - it's the primary key from availability-services table
      // If it's missing, try to find it from availabilityServices by matching service_id
      let assignmentId = editingService.assignment_id;

      if (!assignmentId) {
        // Try to find the assignment_id from availabilityServices
        const matchingAvailService = availabilityServices.find(
          (availService) => availService.service_id === editingService.id,
        );

        if (matchingAvailService) {
          assignmentId = matchingAvailService.id;
          console.log(
            "Found assignment_id from availabilityServices:",
            assignmentId,
          );
        }
      }

      if (!assignmentId) {
        toast.error(
          "Cannot update service: assignment ID is missing. Please refresh the page and try again.",
        );
        console.error(
          "Missing assignment_id. EditingService:",
          editingService,
          "AvailabilityServices:",
          availabilityServices,
        );
        return;
      }

      // Parse price value
      const priceValue = editPrice ? parseFloat(editPrice) : 0;

      // Convert payment mode to API format
      const paymentType: "PREPAID" | "POSTPAID" =
        editPaymentMode === "prepaid" ? "PREPAID" : "POSTPAID";

      try {
        // Step 1: Update availability-services using PATCH /api/v1/doctor/availability-services/{assignment_id}
        console.log(
          "Updating availability service with assignmentId:",
          assignmentId,
        );

        const availabilityServicePayload = {
          consultation_mode: editConsultationMode,
          slot_duration_minutes: editDuration,
          payment_type: paymentType,
          advance_booking_days: editAdvanceBookingDays,
          minimum_notice_minutes: editMinimumNoticeHours * 60, // Convert hours to minutes
          is_bookable: editAllowBooking,
          appointment_type: editAppointmentType.toUpperCase() as
            | "REGULAR"
            | "FOLLOWUP",
          follow_up_validity:
            editAppointmentType === "followup"
              ? parseInt(editFollowupValidity)
              : undefined,
          nickname: editNickname || undefined,
        };

        console.log(
          "Availability service payload:",
          availabilityServicePayload,
        );

        await new Promise<void>((resolve, reject) => {
          updateAvailabilityServiceMutation.mutate(
            {
              assignmentId: assignmentId,
              payload: availabilityServicePayload,
            },
            {
              onSuccess: () => {
                console.log("Availability service updated successfully");
                resolve();
              },
              onError: (error: any) => {
                console.error("Failed to update availability service:", error);
                reject(error);
              },
            },
          );
        });

        // Step 2: Handle pricing logic based on requirements
        if (priceValue > 0) {
          const hasAvailabilityPriceAmount =
            availabilityPricingData?.price_amount != null;
          const hasServicePriceAmount =
            servicePricingData?.price_amount != null;
          const hasAvailabilityPricingId = availabilityPricingData?.id;

          // Case 1: Both service_price and price_amount are null → POST to both APIs
          if (!hasServicePriceAmount && !hasAvailabilityPriceAmount) {
            // POST to service-pricing
            await new Promise<void>((resolve) => {
              createDoctorServicePricingMutation.mutate(
                {
                  service_id: editingService.id,
                  currency: "XCG",
                  price_amount: priceValue,
                },
                {
                  onSuccess: () => resolve(),
                  onError: () => resolve(), // Non-blocking
                },
              );
            });

            // POST to availability-service-pricing
            await new Promise<void>((resolve) => {
              createAvailabilityServicePricingMutation.mutate(
                {
                  doctor_service_availability_id: assignmentId,
                  currency: "XCG",
                  price_amount: priceValue,
                },
                {
                  onSuccess: () => resolve(),
                  onError: () => resolve(), // Non-blocking
                },
              );
            });
          }
          // Case 2: price_amount exists and user edits price → PATCH availability-pricing only
          else if (hasAvailabilityPriceAmount && hasAvailabilityPricingId) {
            await new Promise<void>((resolve) => {
              updateAvailabilityServicePricingMutation.mutate(
                {
                  pricingId: availabilityPricingData.id as string,
                  payload: { price_amount: priceValue },
                },
                {
                  onSuccess: () => resolve(),
                  onError: () => resolve(), // Non-blocking
                },
              );
            });
          }
          // Case 3: Only service_price exists (price_amount is null) → POST availability-pricing
          else if (hasServicePriceAmount && !hasAvailabilityPriceAmount) {
            await new Promise<void>((resolve) => {
              createAvailabilityServicePricingMutation.mutate(
                {
                  doctor_service_availability_id: assignmentId,
                  currency: "XCG",
                  price_amount: priceValue,
                },
                {
                  onSuccess: () => resolve(),
                  onError: () => resolve(), // Non-blocking
                },
              );
            });
          }
        }

        // Update local state
        const updatedServices = services.map((s) =>
          s.id === editingService.id
            ? {
                ...s,
                consultation_mode: editConsultationMode,
                duration: editDuration,
                amount: priceValue,
                payment_mode: editPaymentMode,
                nickname: editNickname,
                allow_patient_booking: editAllowBooking,
                advance_booking_days: editAdvanceBookingDays,
                minimum_notice_minutes: editMinimumNoticeHours * 60,
                appointment_type: editAppointmentType,
                follow_up_validity:
                  editAppointmentType === "followup"
                    ? parseInt(editFollowupValidity)
                    : undefined,
              }
            : s,
        );
        setServices(updatedServices);
        setEditingService(null);
        // Toast is already shown by the mutation hooks, no need to show it here
        onScheduleUpdated?.();
      } catch (error: any) {
        // Error toast is already shown by the mutation hooks, no need to show it here
        console.error("Failed to update service:", error);
      }
    };

    const handleRemoveService = async (
      service: DoctorScheduleAppointmentService,
    ) => {
      // If it has both assignment_id and doctor_service_id, use DELETE APIs
      if (service.assignment_id && service.doctor_service_id) {
        const assignmentId = service.assignment_id; // Primary key id from availability-services
        const doctorServiceId = service.doctor_service_id; // Primary key id from doctor-services

        try {
          // Step 1: Try to delete pricing (non-blocking - continue even if not found)
          // Fetch and delete availability-service pricing
          try {
            const availabilityPricingRes =
              await getAvailabilityServicePricing(assignmentId);
            if (
              availabilityPricingRes?.data &&
              availabilityPricingRes.data.length > 0 &&
              availabilityPricingRes.data[0].id
            ) {
              await new Promise<void>((resolve) => {
                deleteAvailabilityServicePricingMutation.mutate(
                  availabilityPricingRes.data![0].id as string,
                  {
                    onSuccess: () => resolve(),
                    onError: () => resolve(),
                  },
                );
              });
            }
          } catch {
            // Pricing doesn't exist, continue
          }

          // Fetch and delete doctor service pricing
          try {
            const servicePricingRes = await getDoctorServicePricing(service.id);
            if (
              servicePricingRes?.data &&
              servicePricingRes.data.length > 0 &&
              servicePricingRes.data[0].id
            ) {
              await new Promise<void>((resolve) => {
                deleteDoctorServicePricingMutation.mutate(
                  servicePricingRes.data![0].id as string,
                  {
                    onSuccess: () => resolve(),
                    onError: () => resolve(), // Resolve even on error (not found is OK)
                  },
                );
              });
            }
          } catch {
            // Pricing doesn't exist, continue
          }

          // Step 2: Delete from availability-services
          await new Promise<void>((resolve, reject) => {
            deleteAvailabilityServiceMutation.mutate(assignmentId, {
              onSuccess: () => resolve(),
              onError: (error: any) => reject(error),
            });
          });

          // Step 3: Delete from doctor-services
          await new Promise<void>((resolve, reject) => {
            deleteDoctorServiceMutation.mutate(doctorServiceId, {
              onSuccess: () => resolve(),
              onError: (error: any) => reject(error),
            });
          });

          // Update local state after deletions succeed
          const updatedServices = services.filter(
            (s) => s.assignment_id !== assignmentId,
          );
          setServices(updatedServices);
          toast.success("Service removed successfully!");
          onScheduleUpdated?.();
        } catch (error: any) {
          console.error("Failed to remove service:", error);
          toast.error(error?.message || "Failed to remove service");
        }
      } else {
        // Fallback to old method for services without assignment_id
        const updatedServices = services.filter((s) => s.id !== service.id);
        setServices(updatedServices);
        toast.success("Service removed");

        // If it's an existing slot (not draft), update the schedule
        if (!isDraft && initialData.id) {
          updateScheduleMutation.mutate(buildPayload(updatedServices), {
            onSuccess: () => {
              onScheduleUpdated?.();
            },
            onError: () => {
              setServices(services);
              toast.error("Failed to remove service");
            },
          });
        }
      }
    };

    return (
      <>
        <Card className="border-0" withBorder>
          <Card.Section className="p-4">
            <div className="flex flex-col gap-6">
              {/* Time Row + Action Buttons (Original Layout Restored) */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <BaseTimePicker
                    value={startTime}
                    onSelect={(value) => handleTimeChange(value, endTime)}
                  />
                  <span>to</span>
                  <BaseTimePicker
                    value={endTime}
                    onSelect={(value) => handleTimeChange(startTime, value)}
                  />
                </div>

                <div className="flex items-center gap-3">
                  {/* {onCopy && (
                  <ActionIcon variant="transparent" onClick={onCopy}>
                    <CopyIcon size={20} style={{ color: '#0F1011' }} />
                  </ActionIcon>
                )} */}
                  <ActionIcon variant="transparent" onClick={onAddNewSlot}>
                    <PlusIcon size={20} style={{ color: "#0F1011" }} />
                  </ActionIcon>
                  {showDeleteButton && onDelete && (
                    <ActionIcon
                      variant="transparent"
                      onClick={() => onDelete(initialData.id)}
                    >
                      <MinusIcon size={20} style={{ color: "#0F1011" }} />
                    </ActionIcon>
                  )}
                </div>
              </div>

              {/* Services List - Show above the input */}
              {isSaved && services.length > 0 && (
                <div className="flex flex-col gap-2 p-3 bg-[#F4F6F9] rounded-lg border border-gray-200">
                  {services.map((service) => (
                    <div
                      key={service.id}
                      className="flex items-center justify-between py-2 border-b border-gray-300 last:border-b-0"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3 text-sm">
                          <span className="font-medium text-[#0F1011]">
                            {service.service_name}
                          </span>
                          <span className="text-[#64748B]">
                            {service.consultation_mode === "IN_CLINIC"
                              ? "In-Clinic"
                              : service.consultation_mode === "TELECONSULTATION"
                                ? "Teleconsultation"
                                : service.consultation_mode || "In-Clinic"}
                          </span>
                          <span className="text-[#64748B]">
                            {service.duration || 30}m
                          </span>
                          <span className="text-[#64748B] capitalize">
                            {service.payment_mode === "prepaid"
                              ? "Prepaid"
                              : service.payment_mode === "postpaid"
                                ? "Postpaid"
                                : service.payment_mode || "Postpaid"}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-2">
                        <button
                          type="button"
                          onClick={() => handleEditService(service)}
                          className="flex items-center justify-center w-6 h-6 rounded-full hover:bg-gray-200 transition-colors"
                          disabled={
                            updateScheduleMutation.isPending ||
                            assignServiceToAvailabilityMutation.isPending
                          }
                        >
                          <PencilIcon size={16} style={{ color: "#64748B" }} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRemoveService(service)}
                          className="flex items-center justify-center w-6 h-6 rounded-full hover:bg-gray-200 transition-colors"
                          disabled={
                            updateScheduleMutation.isPending ||
                            assignServiceToAvailabilityMutation.isPending ||
                            deleteAvailabilityServiceMutation.isPending ||
                            deleteDoctorServiceMutation.isPending
                          }
                        >
                          <XIcon size={16} style={{ color: "#64748B" }} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Add Service Select - Only show if availability is saved */}
              {isSaved ? (
                <div className="w-full">
                  <Select
                    placeholder="Search or add a service"
                    searchable
                    clearable
                    data={calendarServicesFormatted}
                    value={selectedServiceId}
                    leftSection={
                      <MagnifyingGlassIcon style={{ color: "#0F1011" }} />
                    }
                    nothingFoundMessage={
                      <span className="font-medium">No service found</span>
                    }
                    onChange={handleServiceSelect}
                    disabled={
                      updateScheduleMutation.isPending ||
                      createAvailabilityMutation.isPending ||
                      addDoctorServiceMutation.isPending ||
                      assignServiceToAvailabilityMutation.isPending
                    }
                    styles={{
                      root: {
                        width: "100%",
                      },
                      input: {
                        border: "1px solid #0F1011",
                        borderRadius: "8px",
                        height: "40px",
                        width: "100%",
                      },
                      dropdown: {
                        borderRadius: "8px",
                        border: "1px solid #0F1011",
                      },
                    }}
                  />
                </div>
              ) : (
                <div className="text-sm text-gray-500 italic">
                  Please save the availability time first to add services
                </div>
              )}
            </div>
          </Card.Section>
        </Card>

        {/* Edit Service Drawer */}
        <BaseSideSheet
          size="lg"
          title="Edit Service"
          isOpen={!!editingService}
          onOpenChange={(open) => {
            if (!open) setEditingService(null);
          }}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleUpdateService();
            }}
          >
            <Stack gap="lg">
              {/* Service Name */}
              <Input.Wrapper label="Service Name">
                <Input
                  value={editingService?.service_name || ""}
                  disabled
                  style={{ maxWidth: "50%" }}
                />
              </Input.Wrapper>

              {/* Service Mode / Consultation Mode */}
              <Stack gap="sm">
                <Text fw={600}>Service Mode</Text>
                <Radio.Group
                  value={
                    editConsultationMode === "IN_CLINIC" ? "in-clinic" : "video"
                  }
                  onChange={(value) =>
                    setEditConsultationMode(
                      value === "in-clinic" ? "IN_CLINIC" : "TELECONSULTATION",
                    )
                  }
                >
                  <Group gap="md">
                    <Radio value="in-clinic" label="In-Clinic" />
                    <Radio value="video" label="Video" />
                  </Group>
                </Radio.Group>
              </Stack>

              {/* Price Input */}
              <Stack gap="sm">
                <Text fw={600}>Price</Text>
                <Input.Wrapper>
                  <Input
                    leftSection="XCG."
                    leftSectionWidth={60}
                    leftSectionProps={{
                      style: {
                        paddingLeft: "12px",
                        paddingRight: "8px",
                        color: "#495057",
                      },
                    }}
                    placeholder="200"
                    value={editPrice}
                    onChange={(e) => setEditPrice(e.target.value)}
                    styles={{
                      input: {
                        paddingLeft: "70px !important",
                      },
                    }}
                    style={{ maxWidth: "50%" }}
                  />
                </Input.Wrapper>
              </Stack>

              {/* Duration */}
              <Stack gap="sm">
                <Text fw={600}>Duration</Text>
                <Select
                  placeholder="Select duration"
                  value={String(editDuration)}
                  onChange={(value) =>
                    setEditDuration(value ? parseInt(value) : 30)
                  }
                  data={[
                    { label: "2 Minutes", value: "2" },
                    { label: "3 Minutes", value: "3" },
                    { label: "5 Minutes", value: "5" },
                    { label: "7 Minutes", value: "7" },
                    { label: "10 Minutes", value: "10" },
                    { label: "15 Minutes", value: "15" },
                    { label: "20 Minutes", value: "20" },
                    { label: "25 Minutes", value: "25" },
                    { label: "30 Minutes", value: "30" },
                    { label: "35 Minutes", value: "35" },
                    { label: "40 Minutes", value: "40" },
                    { label: "45 Minutes", value: "45" },
                    { label: "50 Minutes", value: "50" },
                    { label: "55 Minutes", value: "55" },
                    { label: "60 Minutes", value: "60" },
                    { label: "65 Minutes", value: "65" },
                    { label: "70 Minutes", value: "70" },
                    { label: "75 Minutes", value: "75" },
                    { label: "80 Minutes", value: "80" },
                    { label: "85 Minutes", value: "85" },
                    { label: "90 Minutes", value: "90" },
                    { label: "2 hours", value: "120" },
                    { label: "3 hours", value: "180" },
                    { label: "4 hours", value: "240" },
                    { label: "5 hours", value: "300" },
                    { label: "6 hours", value: "360" },
                  ]}
                  style={{ maxWidth: "50%" }}
                  maxDropdownHeight={400}
                />
              </Stack>

              {/* Advanced Settings */}

              {/* Footer Buttons */}
              <Group justify="flex-end" gap="md" mt="xl">
                <Button
                  variant="outline"
                  onClick={() => setEditingService(null)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={updateAvailabilityServiceMutation.isPending}
                  style={{ backgroundColor: "#002FD4" }}
                >
                  {updateAvailabilityServiceMutation.isPending
                    ? "Updating..."
                    : "Update"}
                </Button>
              </Group>
            </Stack>
          </form>
        </BaseSideSheet>
      </>
    );
  },
);

WeeklyScheduleItemSlot.displayName = "WeeklyScheduleItemSlot";

export default WeeklyScheduleItemSlot;
