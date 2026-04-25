// src/features/app/calendar/components/calendar-services/index.tsx
import ErrorWhileFetchingData from "@/components/orvo/common/error-while-fetching-data";
import {
  Box,
  Flex,
  LoadingOverlay,
  Text,
  Card,
  Group,
  Stack,
  ActionIcon,
} from "@mantine/core";
import { PencilIcon } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import {
  getDoctorServices,
  getDoctorServicePricing,
} from "@/services/weekly-schedule";
import type { DoctorService } from "@/services/weekly-schedule";
import { useEffect, useState } from "react";
import EditServiceModal from "./edit-service-modal";

interface CalendarServicesProps {
  isActive?: boolean;
}

interface ServiceWithPricing {
  id: string;
  service_name: string;
  amount: number;
  duration: number;
  currency: string;
  service_mode: string;
  appointment_type: string;
  pricing_id?: string;
}

const CalendarServices = ({ isActive = false }: CalendarServicesProps) => {
  const [servicesWithPricing, setServicesWithPricing] = useState<
    ServiceWithPricing[]
  >([]);
  const [editingService, setEditingService] =
    useState<ServiceWithPricing | null>(null);

  // Use GET /v1/doctor/services for the services tab - refetch when tab becomes active
  const {
    data: services = [],
    isLoading,
    error,
    refetch,
  } = useQuery<DoctorService[]>({
    queryKey: ["doctor-services"],
    queryFn: getDoctorServices,
    staleTime: 0, // Don't use stale data
    gcTime: 0, // Don't cache
    enabled: isActive,
    refetchOnMount: true,
    refetchOnWindowFocus: false,
  });

  // Refetch when Services tab is clicked
  useEffect(() => {
    if (isActive) {
      refetch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive]);

  // Fetch pricing for each service - refetch when services change or tab becomes active
  useEffect(() => {
    const fetchPricing = async () => {
      if (services.length === 0) {
        setServicesWithPricing([]);
        return;
      }

      const servicesWithPrices = await Promise.all(
        services.map(async (service) => {
          try {
            // Always fetch fresh pricing data
            const pricingResponse = await getDoctorServicePricing(
              service.service_id || service.id || "",
            );
            const pricing = pricingResponse?.data?.[0];

            return {
              id: service.service_id || service.id,
              service_name: service.service_name || "Unknown Service",
              amount: pricing?.price_amount || pricing?.price || 0,
              duration: service.slot_duration_minutes || 30,
              currency: pricing?.currency || "USD",
              service_mode: service.service_mode || "",
              appointment_type: service.appointment_type || "",
              pricing_id: pricing?.id, // Store pricing_id for updates
            };
          } catch (error) {
            // If pricing fetch fails, return service with 0 price
            return {
              id: service.service_id || service.id,
              service_name: service.service_name || "Unknown Service",
              amount: 0,
              duration: service.slot_duration_minutes || 30,
              currency: "USD",
              service_mode: service.service_mode || "",
              appointment_type: service.appointment_type || "",
              pricing_id: undefined,
            };
          }
        }),
      );

      setServicesWithPricing(servicesWithPrices);
    };

    if (isActive) {
      fetchPricing();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [services]);

  const calendarServices = servicesWithPricing;

  if (error) return <ErrorWhileFetchingData />;

  if (isLoading) return <LoadingOverlay visible />;

  if (!calendarServices || calendarServices.length === 0) {
    return (
      <Flex w="100%" h="65vh" justify="center" align="center">
        <Text fw={700} size="xl" c="dimmed">
          No services found. Create your first service!
        </Text>
      </Flex>
    );
  }

  return (
    <>
      <Stack gap="md" py="lg" px="md">
        {calendarServices.map((service) => (
          <Card
            key={service.id}
            withBorder
            radius="md"
            shadow="sm"
            className="hover:shadow-md transition-shadow"
          >
            <Group justify="space-between" align="center">
              <Box>
                <Text fw={600} size="lg">
                  {service.service_name}
                </Text>
                <Text size="sm" c="dimmed">
                  {service.currency === "USD" ? "$" : "XCG"}
                  {service.amount} • {service.duration} mins
                </Text>
              </Box>

              <ActionIcon
                variant="light"
                color="blue"
                size="lg"
                onClick={() => setEditingService(service)}
              >
                <PencilIcon size={18} weight="bold" />
              </ActionIcon>
            </Group>
          </Card>
        ))}
      </Stack>

      {/* Edit Service Modal */}
      <EditServiceModal
        isOpen={!!editingService}
        onClose={() => setEditingService(null)}
        service={editingService}
        onSuccess={async () => {
          // Force immediate refetch of services and pricing
          setServicesWithPricing([]); // Clear current data
          const result = await refetch();

          // Wait a bit for the refetch to complete
          if (result.data) {
            // Trigger pricing refetch by updating services
            // The useEffect will handle fetching pricing
          }
        }}
      />
    </>
  );
};

export default CalendarServices;
