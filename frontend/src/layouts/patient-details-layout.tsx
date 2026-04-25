import PatientDetailSidebarInfoCard from '@/features/app/patient/components/patient-detail-sidebar-info-card-eclinic'
import { Divider, NavLink } from '@mantine/core'
import {
  CaretRightIcon,
  CheckIcon,
  DotsNineIcon,
  FileIcon,
  FilePlusIcon,
  ListBulletsIcon,
  StethoscopeIcon,
  ToothIcon,
  UserPlusIcon
} from '@phosphor-icons/react'
import { Link, Outlet, useLocation, useParams } from '@tanstack/react-router'
import React, { type FC, type ReactElement } from 'react'

const patientDetailsPages = [
  {
    enabled: true,
    href: 'visits',
    label: 'Past Visits',
    icon: (
      <FilePlusIcon
        size={20}
        weight={'fill'}
      />
    )
  },
  {
    enabled: true,
    href: 'patient-overview',
    label: 'Patient Overview',
    icon: (
      <DotsNineIcon
        size={20}
        weight={'bold'}
      />
    )
  },
  {
    enabled: true,
    href: 'vitals-and-lab-trends',
    label: 'Vitals Signs',
    icon: (
      <ToothIcon
        size={20}
        weight={'fill'}
      />
    )
  },
  {
    enabled: true,
    href: 'medical-history',
    label: 'Add Medical History',
    icon: (
      <StethoscopeIcon
        size={20}
        weight={'bold'}
      />
    )
  }
]

const additionalPatientDetailsPages = [
  // {
  //   enabled: true,
  //   href: 'receipts',
  //   label: 'Receipts',
  //   icon: (
  //     <CurrencyInrIcon
  //       size={20}
  //       weight={'bold'}
  //     />
  //   )
  // },
  {
    enabled: true,
    href: 'medical-certificates',
    label: 'Medical Documents',
    icon: (
      <FileIcon
        size={20}
        weight={'bold'}
      />
    )
  },
  {
    enabled: true,
    href: 'sent-files',
    label: 'SOAP Notes',
    icon: (
      <ListBulletsIcon
        size={20}
        weight={'bold'}
      />
    )
  }
]

const PatientDetailsLayout: FC = (): ReactElement => {
  const { pathname } = useLocation()
  const { patientId } = useParams({ strict: false })

  const isNewPatient = pathname === '/app/patient/new'
  return (
    <div className="flex h-screen gap-0">

      <div className="flex flex-col bg-white h-screen w-[300px] gap-0 border-r border-r-gray-200">
        {/* <Button
          variant="subtle"
          leftSection={<ArrowLeftIcon size={20} weight="bold" />}
          onClick={() => window.history.back()}
          className="justify-start px-4 py-2 text-gray-700 hover:bg-gray-100"
        >
          Back
        </Button> */}
        <PatientDetailSidebarInfoCard />

        <Divider />

        {isNewPatient && (
          <NavLink
            disabled
            component={Link}
            label={'Add Patient Info'}
            leftSection={
              <UserPlusIcon
                size={20}
                weight={'fill'}
              />
            }
            to={''}
            variant={'subtle'}
          />
        )}

        {/* Patient Details Pages links */}
        {patientDetailsPages &&
          !isNewPatient &&
          patientDetailsPages.map(({ href, icon, label }) => {
            const isActive = pathname.includes(
              `/app/patients/${patientId}/${href}`
            )

            return (
              <React.Fragment key={href}>
                <NavLink
                  component={Link}
                  to={`/app/patients/${patientId}/${href}`}
                  label={label}
                  leftSection={React.cloneElement(icon, {
                    color: '#002FD4',
                    size: 20
                  })}
                  rightSection={
                    isActive ? (
                      <CheckIcon
                        size={20}
                        color="#002FD4"
                        weight="bold"
                      />
                    ) : (
                      <CaretRightIcon
                        size={20}
                        color="#0F1011"
                        weight="bold"
                      />
                    )
                  }
                  variant="subtle"
                  active={isActive}
                  style={{
                    backgroundColor: isActive ? '#F4F6F9' : 'transparent'
                  }}
                  styles={{
                    label: {
                      fontFamily: 'Poppins, sans-serif',
                      fontWeight: isActive ? 700 : 400,
                      fontSize: '14px',
                      lineHeight: '20px',
                      color: isActive ? '#002FD4' : '#0F1011'
                    }
                  }}
                />
                <Divider />
              </React.Fragment>
            )
          })}

        {!isNewPatient && (
          <div className="p-sm mt-[30px]">
            <div className="text-gray-600 font-extrabold text-xs">
              Other Details
            </div>
          </div>
        )}

        {additionalPatientDetailsPages &&
          !isNewPatient &&
          additionalPatientDetailsPages.map(({ href, icon, label }) => {
            const isActive = pathname.includes(
              `/app/patients/${patientId}/${href}`
            )

            return (
              <React.Fragment key={href}>
                <NavLink
                  component={Link}
                  to={`/app/patients/${patientId}/${href}`}
                  label={label}
                  leftSection={React.cloneElement(icon, {
                    color: '#002FD4',
                    size: 20
                  })}
                  rightSection={
                    isActive ? (
                      <CheckIcon
                        size={20}
                        color="#002FD4"
                        weight="bold"
                      />
                    ) : (
                      <CaretRightIcon
                        size={20}
                        color="#0F1011"
                        weight="bold"
                      />
                    )
                  }
                  variant="subtle"
                  active={isActive}
                  style={{
                    backgroundColor: isActive ? '#F4F6F9' : 'transparent'
                  }}
                  styles={{
                    label: {
                      fontFamily: 'Poppins, sans-serif',
                      fontWeight: isActive ? 700 : 400,
                      fontSize: '14px',
                      lineHeight: '20px',
                      color: isActive ? '#002FD4' : '#0F1011'
                    }
                  }}
                />
                <Divider />
              </React.Fragment>
            )
          })}
      </div>

      <div className="bg-gray-100 h-screen w-full">
        <Outlet />
      </div>
    </div>
  )
}

export default PatientDetailsLayout
