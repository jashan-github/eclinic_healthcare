declare module 'pagedjs' {
  export class Previewer {
    constructor()
    preview(
      content: Element,
      stylesheets?: string[],
      container?: Element
    ): Promise<Flow>
  }

  export interface Flow {
    total: number
    // Add other properties as needed
  }
}
