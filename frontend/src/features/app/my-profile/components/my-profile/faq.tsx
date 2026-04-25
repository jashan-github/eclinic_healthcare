import { Accordion, Text } from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import { useMyProfile } from '../../hooks/use-my-profile'

type FAQ = {
  id: string
  question: string
  answer: string
}

const FAQs: FC = (): ReactElement => {
  const { myProfile } = useMyProfile()
  const doctorNameWithSalutation = `Dr. ${myProfile.name}`

  const faqsList: FAQ[] = [
    {
      id: 'major-area-of-practice',
      question: `Which area does ${doctorNameWithSalutation} Practice?`,
      answer: `${doctorNameWithSalutation} is ${myProfile.major_specialization}`
    },
    {
      id: 'common-treatments-offered-by-doctor',
      question: `Why do patients visit ${doctorNameWithSalutation}?`,
      answer: `Patients consult ${doctorNameWithSalutation} for the treatment of ${myProfile.commonly_treats?.join(',')}.`
    },
    {
      id: 'doctor-specialisations',
      question: `What is ${doctorNameWithSalutation} specialization?`,
      answer: `${doctorNameWithSalutation} specializes in the treatment of ${myProfile.commonly_treats?.join(',')}.`
    },
    {
      id: 'doctor-educational-qualifications',
      question: `What is ${doctorNameWithSalutation} education qualification?`,
      answer: `${doctorNameWithSalutation} is a ${myProfile.major_specialization} by training and has completed his BE from VTU in 2013.`
    },
    {
      id: 'doctor-clinic-address',
      question: `What is the address of ${doctorNameWithSalutation} clinic?`,
      answer: `${doctorNameWithSalutation} currently practices at ${myProfile.active_clinic?.primary_address?.address}`
    },
    {
      id: 'doctor-total-experience',
      question: `How many years of experience ${doctorNameWithSalutation} have?`,
      answer: `${doctorNameWithSalutation} has over 10 years of clinical experience.`
    },
    {
      id: 'doctor-book-appointment',
      question: `How to book ${doctorNameWithSalutation} appointment?`,
      answer: `To book an appointment with ${doctorNameWithSalutation}, you can book an online appointment with ORVO or visit his clinic offline at: ${myProfile.active_clinic?.primary_address?.address}`
    },
    {
      id: 'doctor-book-appointment-online',
      question: `Can I book ${doctorNameWithSalutation} for online consultation?`,
      answer: `Yes, you can book an online consultation with ${doctorNameWithSalutation}. You can either book it through ORVO website and your appointment will be confirmed by the healthcare provider instantly.`
    },
    {
      id: 'doctor-appointment-fees',
      question: `What is the consultation fees for ${doctorNameWithSalutation}?`,
      answer: `The consultation fee for ${doctorNameWithSalutation} may vary depending on the type of consultation. It is best to contact the clinic post your appointment for the exact charges.`
    },
    {
      id: 'doctor-availability',
      question: `What are the consultation timings of ${doctorNameWithSalutation} for an appointment?`,
      answer: `The consultation timings for ${doctorNameWithSalutation} may vary depending on the location and type of consultation. You can check his availability on his appointment calendar for booking a slot.`
    },
    {
      id: 'languages-spoken-by-doctor',
      question: `What languages are spoken by ${doctorNameWithSalutation}?`,
      answer: `${doctorNameWithSalutation} is fluent in ${myProfile.languages.join(',')}`
    }
  ]

  return (
    <>
      <Text
        fw={700}
        size="xl"
        mb="md"
      >
        Frequently Asked Questions
      </Text>
      <Accordion
        multiple
        styles={{
          item: {
            backgroundColor: '#ffffff',
            border: '1px solid #d1d5db',
            borderRadius: '4px',
            padding: '16px',
            marginBottom: '20px'
          },
          content: { color: '#374151', fontSize: '18px' },
          label: { color: '#374151', fontSize: '20px' }
        }}
      >
        {faqsList.map(({ id, question, answer }) => (
          <Accordion.Item
            key={id}
            value={id}
          >
            <Accordion.Control>{question}</Accordion.Control>
            <Accordion.Panel>{answer}</Accordion.Panel>
          </Accordion.Item>
        ))}
      </Accordion>
    </>
  )
}

export default FAQs
