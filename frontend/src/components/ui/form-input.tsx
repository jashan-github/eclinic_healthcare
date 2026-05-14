import { type ReactNode, type InputHTMLAttributes, type TextareaHTMLAttributes } from 'react'

interface BaseFormInputProps {
  label?: string
  labelClassName?: string
  error?: string
  icon?: ReactNode
  iconPosition?: 'left' | 'right'
  containerClassName?: string
}

interface FormInputProps extends BaseFormInputProps, Omit<InputHTMLAttributes<HTMLInputElement>, 'className'> {
  as?: 'input'
  inputClassName?: string
}

interface FormTextareaProps extends BaseFormInputProps, Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'className'> {
  as: 'textarea'
  inputClassName?: string
}

type FormInputComponentProps = FormInputProps | FormTextareaProps

const FormInput = (props: FormInputComponentProps) => {
  const {
    label,
    labelClassName = 'block mb-2 font-poppins font-medium text-[14px] text-[#545D69]',
    error,
    icon,
    iconPosition = 'right',
    containerClassName = '',
    inputClassName = '',
  } = props

  const baseInputClasses = `w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] 
    font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
    placeholder:text-[#A5ABB3D9] placeholder:font-medium
    focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all
    ${error ? 'border-red-500' : ''}
    ${inputClassName}`

  const isTextarea = props.as === 'textarea'
  const finalInputClasses = isTextarea 
    ? `${baseInputClasses} resize-none`
    : baseInputClasses

  const hasIcon = !!icon
  const inputWrapperClasses = hasIcon 
    ? `relative ${iconPosition === 'left' ? 'pl-10' : 'pr-10'}`
    : ''

  const renderInput = () => {
    if (isTextarea) {
      const {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        as, label, labelClassName, error, icon, iconPosition, containerClassName, inputClassName,
        ...textareaProps
      } = props as FormTextareaProps
      return (
        <textarea
          {...textareaProps}
          className={finalInputClasses}
          rows={textareaProps.rows || 5}
        />
      )
    }

    const {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      as, label, labelClassName, error, icon, iconPosition, containerClassName, inputClassName,
      ...inputAttributes
    } = props as FormInputProps
    return (
      <input
        {...inputAttributes}
        className={finalInputClasses}
      />
    )
  }

  return (
    <div className={containerClassName}>
      {label && (
        <label className={labelClassName}>
          {label}
        </label>
      )}
      <div className={inputWrapperClasses}>
        {hasIcon && iconPosition === 'left' && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[#64748B] pointer-events-none">
            {icon}
          </div>
        )}
        {renderInput()}
        {hasIcon && iconPosition === 'right' && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-[#64748B] pointer-events-none">
            {icon}
          </div>
        )}
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-500 font-poppins">{error}</p>
      )}
    </div>
  )
}

export default FormInput

