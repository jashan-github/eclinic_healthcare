import { type FC, type ReactElement } from 'react'

const ComingSoonPage: FC = (): ReactElement => {
  return (
    <div className="text-gray-900 font-sans leading-relaxed p-6">
      <h3 className="mb-4">Feel Free to Contact Us</h3>
      <ul className="space-y-2 list-style: none; padding-left: 0; line-height: 1.8;">
        <li><strong>By Email:</strong> <a href="mailto:Customer@purehealthbv.com">Customer@purehealthbv.com</a></li>
        <li><strong>By Website:</strong> <a href="http://www.purehealthbv.com/contact" target="_blank">www.purehealthbv.com/contact</a></li>
        <li><strong>By Phone:</strong> <a href="tel:+17215543045">+1 721 554 3045</a></li>
      </ul>
    </div>
  )
}

export default ComingSoonPage
