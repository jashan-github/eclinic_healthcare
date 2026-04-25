import {
  Button,
  Group,
  Table,
  Text,
  Pagination,
  Modal,
  Stack,
  ActionIcon,
} from "@mantine/core";
import { useNavigate } from "@tanstack/react-router";
import { useState, type FC, type ReactElement } from "react";
import { usePatients } from "../../hooks/use-patients";
import PatientTableActions from "./patient-table-actions";
import { formatDate } from "@/utils/helper";
import { useDisclosure } from "@mantine/hooks";
import type { MedicalInfo, Patient } from "../../services/patients-service";
import { Grid } from "@mantine/core";
import { ChatCircleIcon } from "@phosphor-icons/react";
import { useChatService } from "../../hooks/use-chat-service";

const formatYears = (years: number): string => {
  return years === 1 ? "year" : "years";
};

const getMedicalSummary = (info: MedicalInfo | undefined): string[] => {
  if (!info) return [];

  const summary: string[] = [];

  if (info.smoke_years) {
    summary.push(
      `Smoking (${info.smoke_years} ${formatYears(info.smoke_years)})`,
    );
  }
  if (info.alcohol_years) {
    summary.push(
      `Alcohol (${info.alcohol_years} ${formatYears(info.alcohol_years)})`,
    );
  }
  if (info.hypertension_years) {
    summary.push(
      `Hypertension (${info.hypertension_years} ${formatYears(info.hypertension_years)})`,
    );
  }
  if (info.diabetes_mellitus_years) {
    summary.push(
      `Diabetes (${info.diabetes_mellitus_years} ${formatYears(info.diabetes_mellitus_years)})`,
    );
  }
  if (info.hypothyroidism_years) {
    summary.push(
      `Hypothyroidism (${info.hypothyroidism_years} ${formatYears(info.hypothyroidism_years)})`,
    );
  }
  if (info.existing_condition && info.existing_condition_years) {
    summary.push(
      `${info.existing_condition} (${info.existing_condition_years} ${formatYears(info.existing_condition_years)})`,
    );
  }

  info.custom_conditions?.forEach((cond) => {
    if (cond.years) {
      summary.push(`${cond.name} (${cond.years} ${formatYears(cond.years)})`);
    }
  });

  return summary;
};

const PatientsTable: FC = (): ReactElement => {
  const navigate = useNavigate();
  const { patients, isLoading, page, setPage, totalPages } = usePatients();

  const [opened, { open, close }] = useDisclosure(false);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const { createChat } = useChatService();

  return (
    <div className="w-full">
      {/* Desktop Table View */}
      <div className="hidden md:block w-full overflow-x-auto">
        <div
          className="rounded-lg overflow-hidden"
          style={{
            border: "1px solid #E4E5ED",
            borderRadius: "8px",
          }}
        >
          <Table verticalSpacing="sm">
            {/* Table Head */}
            <Table.Thead>
              <Table.Tr
                style={{
                  backgroundColor: "#E8EEFD",
                  borderRadius: "8px 8px 0 0",
                  overflow: "hidden",
                  padding: "2px",
                }}
              >
                <Table.Th className="font-poppins font-bold text-xs leading-[18px] text-center text-[#0F1011] px-4 md:px-8">
                  Sr No
                </Table.Th>
                <Table.Th className="font-poppins font-bold text-xs leading-[18px] text-center text-[#0F1011] px-4 md:px-8">
                  Patient Details
                </Table.Th>
                <Table.Th className="font-poppins font-bold text-xs leading-[18px] text-center text-[#0F1011] px-4 md:px-8">
                  Contact
                </Table.Th>
                <Table.Th className="font-poppins font-bold text-xs leading-[18px] text-center text-[#0F1011] px-4 md:px-8">
                  Last Visited
                </Table.Th>
                <Table.Th className="font-poppins font-bold text-xs leading-[18px] text-center text-[#0F1011] px-4 md:px-8">
                  Medical History
                </Table.Th>
                <Table.Th className="font-semibold text-gray-700 px-4"></Table.Th>
                <Table.Th className="font-poppins font-bold text-xs leading-[18px] text-center text-[#0F1011] px-4 md:px-8">
                  Actions
                </Table.Th>
              </Table.Tr>
            </Table.Thead>

            {/* Table Body */}
            <Table.Tbody
              style={{
                borderTop: "1px solid #E4E5ED",
                borderRadius: "0 0 8px 8px",
                overflow: "hidden",
              }}
            >
              {isLoading ? (
                <Table.Tr>
                  <Table.Td colSpan={7} ta="center" py="xl">
                    <Text size="sm">Loading patients...</Text>
                  </Table.Td>
                </Table.Tr>
              ) : patients.length > 0 ? (
                patients.map((patient, index) => (
                  <Table.Tr key={patient.id} className="py-2">
                    <Table.Td
                      className="px-4 md:px-8"
                      style={{
                        fontFamily: "Poppins",
                        fontSize: "13px",
                        color: "#0F1011",
                      }}
                    >
                      {(page - 1) * 20 + index + 1}
                    </Table.Td>

                    <Table.Td
                      onClick={() =>
                        navigate({ to: `/app/patients/${patient.id}` })
                      }
                      className="px-4 md:px-8 cursor-pointer"
                    >
                      <div className="block text-center">
                        <span
                          style={{
                            fontFamily: "Poppins",
                            fontWeight: 600,
                            fontSize: "14px",
                            color: "#002FD4",
                            textTransform: "capitalize",
                          }}
                        >
                          {patient.name},
                        </span>{" "}
                        <span
                          style={{
                            fontFamily: "Poppins",
                            fontSize: "14px",
                            color: "#0F1011",
                          }}
                        >
                          {patient.gender} , {patient.age}Y
                        </span>
                      </div>
                    </Table.Td>

                    <Table.Td
                      className="px-4 md:px-8"
                      style={{
                        fontFamily: "Poppins",
                        fontSize: "13px",
                        color: "#0F1011",
                      }}
                    >
                      {patient.phone || patient.email || "-"}
                    </Table.Td>

                    <Table.Td
                      className="px-4 md:px-8"
                      style={{
                        fontFamily: "Poppins",
                        fontSize: "13px",
                        color: "#0F1011",
                      }}
                    >
                      {formatDate(patient.last_visited_date!)}
                    </Table.Td>

                    <Table.Td
                      className="px-4 md:px-8"
                      style={{
                        fontFamily: "Poppins",
                        fontSize: "13px",
                        color: "#0F1011",
                        verticalAlign: "middle",
                      }}
                    >
                      {!patient.has_medical_history || !patient.medical_info ? (
                        <Text c="dimmed">No</Text>
                      ) : !patient.medical_info ||
                        Object.keys(patient.medical_info).length === 0 ? (
                        <Text>Yes (details empty)</Text>
                      ) : (
                        <Stack gap={2}>
                          {getMedicalSummary(patient.medical_info)
                            .slice(0, 2)
                            .map((item, i) => (
                              <Text
                                key={i}
                                style={{
                                  fontFamily: "Poppins",
                                  fontSize: "13px",
                                  color: "#0F1011",
                                  lineHeight: "1.4",
                                }}
                              >
                                • {item}
                              </Text>
                            ))}

                          {/* See more button if more than 2 */}
                          {getMedicalSummary(patient.medical_info).length >
                            2 && (
                            <Button
                              variant="subtle"
                              size="xs"
                              color="#002FD4"
                              onClick={() => {
                                setSelectedPatient(patient);
                                open();
                              }}
                              style={{
                                fontFamily: "Poppins",
                                fontSize: "12px",
                                fontWeight: 500,
                                padding: "2px 8px",
                                height: "auto",
                                width: "fit-content",
                                marginTop: "2px",
                              }}
                            >
                              See more (+
                              {getMedicalSummary(patient.medical_info).length -
                                2}
                              )
                            </Button>
                          )}
                        </Stack>
                      )}
                    </Table.Td>

                    <Table.Td className="px-4">
                      <Group gap={4} justify="center" wrap="nowrap">
                        {patient.today_appointment_id && (
                          <Button
                            variant="transparent"
                            size="xs"
                            onClick={() =>
                              navigate({ to: `/app/patients/${patient.id}` })
                            }
                            style={{
                              fontFamily: "Poppins",
                              fontWeight: 700,
                              fontSize: "13px",
                              color: "#002FD4",
                              cursor: "pointer",
                            }}
                          >
                            Start Visit
                          </Button>
                        )}
                      </Group>
                    </Table.Td>

                    <Table.Td ta="center" className="px-4 md:px-8">
                      <PatientTableActions patient={patient} />
                    </Table.Td>
                  </Table.Tr>
                ))
              ) : (
                <Table.Tr>
                  <Table.Td colSpan={7} ta="center" c="dimmed" py="xl">
                    <Text size="sm">No patients found</Text>
                  </Table.Td>
                </Table.Tr>
              )}
            </Table.Tbody>
          </Table>
        </div>
      </div>
      {/* Mobile Card View */}
      <div className="md:hidden space-y-4">
        {isLoading ? (
          <div className="text-center py-8">
            <Text size="sm">Loading patients...</Text>
          </div>
        ) : patients.length > 0 ? (
          patients.map((patient, index) => (
            <div
              key={patient.id}
              className="bg-white rounded-lg border border-[#E4E5ED] p-4 space-y-3"
            >
              {/* Patient Header */}
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-poppins font-semibold text-sm text-[#0F1011]">
                      {(page - 1) * 20 + index + 1}.
                    </span>
                    <span
                      style={{
                        fontFamily: "Poppins",
                        fontWeight: 600,
                        fontSize: "14px",
                        color: "#002FD4",
                        textTransform: "capitalize",
                      }}
                    >
                      {patient.name}
                    </span>
                    <span
                      style={{
                        fontFamily: "Poppins",
                        fontSize: "13px",
                        color: "#0F1011",
                      }}
                    >
                      {patient.gender}, {patient.age}Y
                    </span>
                  </div>
                  <div className="text-xs text-gray-600 font-poppins">
                    {patient.phone || patient.email || "No contact"}
                  </div>
                </div>
                <PatientTableActions patient={patient} />
              </div>

              {/* Last Visited */}
              <div className="flex items-center gap-2 text-xs text-gray-600">
                <span className="font-poppins font-medium">Last Visited:</span>
                <span className="font-poppins">
                  {formatDate(patient.last_visited_date!)}
                </span>
              </div>

              {/* Medical History */}
              <div>
                <div className="text-xs font-poppins font-medium text-gray-700 mb-1">
                  Medical History:
                </div>
                {!patient.has_medical_history || !patient.medical_info ? (
                  <Text c="dimmed" size="xs">
                    No
                  </Text>
                ) : !patient.medical_info ||
                  Object.keys(patient.medical_info).length === 0 ? (
                  <Text size="xs">Yes (details empty)</Text>
                ) : (
                  <div className="space-y-1">
                    {getMedicalSummary(patient.medical_info)
                      .slice(0, 2)
                      .map((item, i) => (
                        <Text
                          key={i}
                          style={{
                            fontFamily: "Poppins",
                            fontSize: "12px",
                            color: "#0F1011",
                            lineHeight: "1.4",
                          }}
                        >
                          • {item}
                        </Text>
                      ))}
                    {getMedicalSummary(patient.medical_info).length > 2 && (
                      <Button
                        variant="subtle"
                        size="xs"
                        color="#002FD4"
                        onClick={() => {
                          setSelectedPatient(patient);
                          open();
                        }}
                        style={{
                          fontFamily: "Poppins",
                          fontSize: "11px",
                          fontWeight: 500,
                          padding: "2px 8px",
                          height: "auto",
                          width: "fit-content",
                          marginTop: "2px",
                        }}
                      >
                        See more (+
                        {getMedicalSummary(patient.medical_info).length - 2})
                      </Button>
                    )}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="pt-2 border-t border-gray-200">
                {patient.is_appointment_request && (
                  <div className="flex justify-center">
                    <ActionIcon
                      variant="transparent"
                      size="lg"
                      onClick={() => {
                        if (patient && patient.id) {
                          createChat(patient.id);
                        }
                      }}
                      style={{
                        color: "#002FD4",
                        cursor: "pointer",
                      }}
                    >
                      <ChatCircleIcon size={24} weight="bold" />
                    </ActionIcon>
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8">
            <Text size="sm" c="dimmed">
              No patients found
            </Text>
          </div>
        )}
      </div>
      {/* Pagination - Clean & Matches Design */}
      {totalPages > 1 && (
        <div className="mt-6 flex justify-center">
          <Pagination
            total={totalPages}
            value={page}
            onChange={setPage}
            size="sm"
            withEdges
            color="#002FD4"
            radius="md"
          />
        </div>
      )}
      <Modal
        opened={opened}
        onClose={close}
        title={
          <Text fw={600} style={{ fontFamily: "Poppins" }}>
            Medical History Details
          </Text>
        }
        size="md"
        centered
        padding="md"
      >
        {selectedPatient && selectedPatient.medical_info && (
          <Stack gap="sm">
            {getMedicalSummary(selectedPatient.medical_info).length > 0 ? (
              <Grid columns={2} gutter="xs">
                {getMedicalSummary(selectedPatient.medical_info).map(
                  (item, i) => (
                    <Grid.Col key={i} span={1}>
                      <Text
                        style={{
                          fontFamily: "Poppins",
                          fontSize: "13px",
                          color: "#0F1011",
                          lineHeight: "1.4",
                        }}
                      >
                        • {item}
                      </Text>
                    </Grid.Col>
                  ),
                )}
              </Grid>
            ) : (
              <Text
                c="dimmed"
                size="sm"
                style={{
                  fontFamily: "Poppins",
                  fontSize: "13px",
                  color: "#0F1011",
                }}
              >
                No detailed conditions recorded
              </Text>
            )}

            {selectedPatient.medical_info.current_medications?.length ? (
              <>
                <Text
                  fw={500}
                  size="sm"
                  mt="md"
                  style={{
                    fontFamily: "Poppins",
                    fontSize: "13px",
                    color: "#0F1011",
                  }}
                >
                  Current Medications:
                </Text>

                <Grid columns={2} gutter="xs">
                  {selectedPatient.medical_info.current_medications.map(
                    (med, i) => (
                      <Grid.Col key={i} span={1}>
                        <Text
                          style={{
                            fontFamily: "Poppins",
                            fontSize: "13px",
                            color: "#0F1011",
                            lineHeight: "1.4",
                          }}
                        >
                          • {med.name} {med.dosage ? `(${med.dosage}` : "("}
                          {med.frequency ? ` / ${med.frequency}x)` : ")"}
                        </Text>
                      </Grid.Col>
                    ),
                  )}
                </Grid>
              </>
            ) : null}
          </Stack>
        )}
      </Modal>
    </div>
  );
};

export default PatientsTable;
