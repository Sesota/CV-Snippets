export class CoreComponent {
    id: string;
    name: string;
    component_type: string;
    is_hidden: boolean;
    order: number;
}
export class ParentComponent extends CoreComponent {
    components: any[];
}
export class ChildComponent extends CoreComponent {}
export class CoreDropdown extends ParentComponent {}
export class CoreDropDownItem extends ChildComponent {
    text: string;
    icon: string;
    url: string;
}
export class CoreWindow extends ParentComponent {
    window_type: string;
    tab_title: string;
    slug: string;
    theme: string;
    language: Language;
}
export class Language {
    code: string;
    direction: string;
    icon: string;
    name: string;
}
export class CoreBody extends ParentComponent {}
export class CoreNavbar extends ParentComponent {
    attrs: {
        brand: string;
        brand_link: string;
    };
}
export class CoreNavbarItem extends ChildComponent {
    is_minimized: boolean;
    text: string;
    icon: string;
    item_type: string;
    tooltip: string;
    style: string;
    url: string;
    dropdown: CoreDropdown;
}
export class CoreFooter extends ParentComponent {}
export class CoreFooterColumn extends ParentComponent {
    title: string;
    grid: string;
}
export class CoreFooterLink extends ChildComponent {
    text: string;
    url: string;
}
export class CoreFooterText extends ChildComponent {
    text: string;
    url: string;
}
export class CoreFooterPicture extends ChildComponent {
    text: string;
    url: string;
}
export class CoreHeading extends ParentComponent {
    title: string;
    text: string;
}
export class CoreSection extends ChildComponent {
    title: string;
    text: string;
    text_align: string;
    link: string;
    link_text: string;
    background_picture_filename: string;
    picture_filename: string;
    picture_position: string;
}
export class CoreHeader extends CoreComponent {
    title: string;
    motto: string;
    logo_filename: string;
    picture_filename: string;
    components: any;
}
export class CoreForm extends ParentComponent {
    title: string;
    text: string;
    submit_url: string;
    method: string;
}
export class CoreInput extends ChildComponent {
    input_type: string;
    value: string;
    pattern: string;
    placeholder: string;
    required: boolean;
    icon: string;
}
