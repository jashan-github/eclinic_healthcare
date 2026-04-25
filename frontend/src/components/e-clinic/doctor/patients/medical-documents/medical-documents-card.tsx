import { CalendarIcon, CaretDownIcon, CaretRightIcon, DownloadIcon, FileTextIcon, HeartIcon, SelectionIcon, StethoscopeIcon, TestTubeIcon } from "@phosphor-icons/react";
import { useState, useMemo } from "react";
import { usePatientDocuments } from '@/hooks/use-doctor-patient-documents'
import GlobalLoader from '@/components/orvo/common/global-loader'

interface ReportItem {
  id: string;
  title: string;
  doctor: string;
  date: string;
  type: string;
  reviewed: boolean;
  file_url: string;
}

interface Section {
  icon: any;
  label: string;
  count: number;
  color: string;
  reports: ReportItem[];
  document_type: string;
}

interface MedicalDocumentsCardProps {
  patientId: string | undefined;
}

export default function MedicalDocumentsCard({ patientId }: MedicalDocumentsCardProps) {
  const [openSection, setOpenSection] = useState<number | null>(null);
  
  const { data: documentsData, isLoading, error } = usePatientDocuments(patientId);
  
  const documents = documentsData?.data?.documents || [];

  // Transform API documents to ReportItem format
  const transformedDocuments: ReportItem[] = useMemo(() => {
    return documents.map(doc => ({
      id: doc.id,
      title: doc.document_type, // document_type is used as title
      doctor: doc.issued_by || 'Unknown',
      date: doc.issued_date || doc.created_at,
      type: doc.document_type,
      reviewed: true, // All documents are considered reviewed by default
      file_url: doc.file_url
    }))
  }, [documents]);

  // Get recent reports (latest 2 documents)
  const recentReports = useMemo(() => {
    return transformedDocuments
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
      .slice(0, 2)
  }, [transformedDocuments]);

  // Icon mapping based on document type keywords (case insensitive)
  const getDocumentIcon = (docType: string): { icon: any; color: string } => {
    const type = docType.toLowerCase();
    
    if (type.includes('lab') || type.includes('blood') || type.includes('test')) {
      return { icon: TestTubeIcon, color: 'text-orange-600' };
    }
    if (type.includes('x-ray') || type.includes('xray') || type.includes('scan') || type.includes('radiology')) {
      return { icon: SelectionIcon, color: 'text-blue-600' };
    }
    if (type.includes('cardio') || type.includes('heart')) {
      return { icon: HeartIcon, color: 'text-green-600' };
    }
    if (type.includes('nursing') || type.includes('physio')) {
      return { icon: StethoscopeIcon, color: 'text-pink-600' };
    }
    // Default icon for other documents
    return { icon: FileTextIcon, color: 'text-gray-600' };
  };

  // Group documents by type and create sections
  const sections: Section[] = useMemo(() => {
    const grouped = transformedDocuments.reduce((acc, doc) => {
      const type = doc.type || 'Other Documents';
      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(doc);
      return acc;
    }, {} as Record<string, ReportItem[]>);

    return Object.entries(grouped).map(([type, reports]) => {
      const { icon, color } = getDocumentIcon(type);
      return {
        icon,
        label: type, // Use the actual document_type as label
        count: reports.length,
        color,
        reports,
        document_type: type
      };
    });
  }, [transformedDocuments]);

  const toggleSection = (index: number) => {
    setOpenSection(openSection === index ? null : index);
  };

  const handleDownload = (fileUrl: string) => {
    // Open file in new tab for download
    window.open(fileUrl, '_blank');
  };

  if (isLoading) {
    return <GlobalLoader />;
  }

  if (error) {
    return (
      <div className="max-w-[1134px] text-center py-8 text-red-500">
        Failed to load medical documents
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="max-w-[1134px] text-center py-8 text-gray-500">
        No medical documents available for this patient
      </div>
    );
  }

  return (
    <div className="max-w-[1134px]">
      <div className="border border-[#E2E8F0] px-6 pt-5 rounded-lg">
        <div className="mb-4 font-poppins font-semibold text-lg leading-7 tracking-[-0.45px] text-[#002FD4]">Recent Reports</div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-6">
          {recentReports.map((report, index) => (
            <div
              key={index}
              className="border border-[#E2E8F0] flex flex-row justify-between rounded-lg p-4"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <p className="font-poppins font-semibold text-sm leading-6 text-[#0F1011]">
                    {report.title}
                    <span className="inline-flex ml-3 items-center px-2.5 py-0.5 rounded-full bg-[#E1E7EF] font-poppins font-normal text-xs leading-4 text-[#0F1011]">
                      Reviewed
                    </span>
                  </p>
                  <p className="font-poppins font-normal text-sm leading-5 text-[#5C6F8A]">
                    {report.doctor}
                  </p>
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-1">
                    <div className="font-poppins inline-flex gap-1 font-normal text-xs leading-4 text-[#5C6F8A]">
                      <CalendarIcon size={16} /> 
                      {new Date(report.date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </div>
                    <div className="font-poppins font-normal text-xs leading-4 text-[#5C6F8A]">
                      Type: {report.type}
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex justify-center">
                <button onClick={() => handleDownload(report.file_url)}>
                  <DownloadIcon className="w-5 h-5" color="#0F1011"/>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Accordion Section List */}
      <div className="space-y-4 mt-6">
        {sections.map((section, index) => {
          const Icon = section.icon;
          const isOpen = openSection === index;

          return (
            <div
              key={index}
              className="border border-[#E2E8F0] rounded-md overflow-hidden"
            >
              {/* Accordion Header */}
              <div
                onClick={() => toggleSection(index)}
                className="flex items-center justify-between p-3 hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-5 h-5 ${section.color}`} />
                  <span className="font-poppins font-semibold text-base leading-7 tracking-[-0.45px] text-[#0F1011]">
                    {section.label}
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-[#E1E7EF] font-poppins font-semibold text-xs leading-4 text-[#0F1011]">
                    {section.count}
                  </span>
                </div>
                {isOpen ? (
                  <CaretDownIcon className="w-5 h-5 text-gray-400" />
                ) : (
                  <CaretRightIcon className="w-5 h-5 text-gray-400" />
                )}
              </div>

              {/* Accordion Content - Smooth Transition */}
              <div
                className={`transition-all duration-300 ease-in-out ${
                  isOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                } overflow-hidden`}
              >
                <div className="px-4 pb-4 pt-2 space-y-3 border-t border-[#E2E8F0]">
                  {section.reports.map((report, i) => (
                    <div
                      key={i}
                      className="flex items-start justify-between p-3 bg-gray-50 rounded-md hover:bg-[#F4F6F9] transition-colors"
                    >
                      <div className="flex-1">
                        <p className="font-poppins font-medium text-sm text-[#0F1011]">
                          {report.title}
                        </p>
                        <p className="font-poppins text-xs text-[#5C6F8A] mt-1">
                          {report.doctor} • {new Date(report.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </p>
                      </div>
                      <button 
                        className="ml-3"
                        onClick={() => handleDownload(report.file_url)}
                      >
                        <DownloadIcon className="w-4 h-4" color="#0F1011" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}