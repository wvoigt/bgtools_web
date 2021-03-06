from django.http import HttpResponse
from django.shortcuts import render
from django import forms
import domdiv.main
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, HTML
from crispy_forms.bootstrap import FormActions, Accordion, AccordionGroup
# from chitboxes.chitboxes import ChitBoxGenerator


class TabGenerationOptionsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(TabGenerationOptionsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML('<h3>Generation Options</h3>'),
                    css_class='col-md-9'
                ),
                Div(
                    FormActions(
                        Submit('submit', 'Generate',
                               style="margin-top: 20px;")
                    ),
                    css_class='col-md-3'
                ),
                css_class='row'
            ),
            Div(
                Div(
                    Accordion(
                        AccordionGroup('Expansion Selection',
                                       'expansions'),
                        AccordionGroup('Global Style',
                                       'cropmarks',
                                       'wrappers',
                                       'tabsonly',
                                       'no_footer'),
                        AccordionGroup('Sizes and Orientation',
                                       'orientation',
                                       'pagesize',
                                       'cardsize'),
                        AccordionGroup('Divider Layout',
                                       'tab_side',
                                       'tab_name_align',
                                       'set_icon',
                                       'cost_icon',
                                       'counts'),
                        AccordionGroup('Text Options',
                                       'divider_front_text',
                                       'divider_back_text',
                                       'language'),
                        AccordionGroup('Order, Groups and Extras',
                                       'order',
                                       'group_special',
                                       'expansion_dividers'),

                    ),
                    css_class='col-md-12',
                ),
                css_class='row',
            )
        )
        self.helper.form_id = 'id-tabgenoptions'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        self.helper.form_action = '/'
        for field in self.fields.itervalues():
            field.required = False

    choices = ['Horizontal', 'Vertical']
    orientation = forms.ChoiceField(choices=zip(choices, choices),
                                    label='Divider Orientation',
                                    initial='Horizontal')
    choices = ['Letter', 'A4', 'A3']
    pagesize = forms.ChoiceField(choices=zip(choices, choices), label='Page Size', initial='Letter')
    choices = ['Sleeved', 'Unsleeved']
    cardsize = forms.ChoiceField(choices=zip(choices, choices), label='Card Size', initial='Unsleeved')
    choices = domdiv.main.EXPANSION_CHOICES
    # make pretty names for the expansion choices
    choiceNames = []
    replacements = {
        '1stedition': '1st Edition',
        '2ndeditionupgrade': '2nd Edition Upgrade',
        '2ndedition': '2nd Edition'
    }
    for choice in choices:
        for s, r in replacements.iteritems():
            if choice.lower().endswith(s):
                choiceNames.append('{} {}'.format(choice[:-len(s)].capitalize(), r))
                break
        else:
            choiceNames.append(choice.capitalize())
    expansions = forms.MultipleChoiceField(
        choices=zip(choices, choiceNames),
        label='Expansions to Include (Cmd/Ctrl click to select multiple)',
        initial=choices,
        widget=forms.SelectMultiple(attrs={'size': '17'})
    )
    edition = forms.ChoiceField(choices=zip(domdiv.main.EDITION_CHOICES, domdiv.main.EDITION_CHOICES),
                                label='Edition',
                                initial='latest')
    cropmarks = forms.BooleanField(label="Cropmarks Instead of Outlines", initial=False)
    wrappers = forms.BooleanField(label="Slipcases Instead of Dividers", initial=False)
    counts = forms.BooleanField(label="Show # of Cards per Divider", initial=False)
    tab_name_align = forms.ChoiceField(choices=zip(domdiv.main.NAME_ALIGN_CHOICES, domdiv.main.NAME_ALIGN_CHOICES))
    tab_side = forms.ChoiceField(choices=zip(domdiv.main.TAB_SIDE_CHOICES, domdiv.main.TAB_SIDE_CHOICES))
    samesidelabels = forms.BooleanField(label="Same Side Labels", initial=False)
    order = forms.ChoiceField(label="Divider Order",
                              choices=zip(domdiv.main.ORDER_CHOICES, domdiv.main.ORDER_CHOICES))
    group_special = forms.BooleanField(label="Group Special Cards (e.g. Prizes)", initial=True)
    expansion_dividers = forms.BooleanField(label="Extra Expansion Dividers", initial=False)
    tabsonly = forms.BooleanField(label="Avery 5167/8867 Tab Label Sheets", initial=False)
    set_icon = forms.ChoiceField(
        choices=zip(domdiv.main.LOCATION_CHOICES, domdiv.main.LOCATION_CHOICES),
        label="Set Icon Location",
        initial="tab"
    )
    cost_icon = forms.ChoiceField(
        choices=zip(domdiv.main.LOCATION_CHOICES, domdiv.main.LOCATION_CHOICES),
        label="Cost Icon Location",
        initial="tab"
    )
    language = forms.ChoiceField(
        choices=zip(domdiv.main.LANGUAGE_CHOICES, domdiv.main.LANGUAGE_CHOICES),
        label='Language',
        initial='en_us'
    )
    events = forms.BooleanField(label="Exclude Individual Events & Landmarks", initial=False)
    divider_front_text = forms.ChoiceField(label='Front Text',
                                           choices=zip(domdiv.main.TEXT_CHOICES, domdiv.main.TEXT_CHOICES),
                                           initial='card')
    divider_back_text = forms.ChoiceField(
        label='Back Text',
        choices=zip(domdiv.main.TEXT_CHOICES + ['none'], domdiv.main.TEXT_CHOICES + ['no back page']),
        initial='rules'
    )
    no_footer = forms.BooleanField(label='Omit set label footer text', initial=False)


class ChitBoxForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ChitBoxForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = '/chitbox'

        self.helper.add_input(Submit('submit', 'Generate'))

    width = forms.FloatField(label='Width in cm', min_value=1.0, max_value=20.0, initial=5)
    length = forms.FloatField(label='Length in cm', min_value=1.0, max_value=20.0, initial=5)
    height = forms.FloatField(label='Height in cm', min_value=1.0, max_value=20.0, initial=2)
    main_image = forms.ImageField(label='Upload Main Image')
    side_image = forms.ImageField(label='Upload Side Image')


def index(request):
    if request.method == 'POST':
        form = TabGenerationOptionsForm(request.POST)
        if form.is_valid():
            # generate default options
            options = domdiv.main.parse_opts([])
            data = form.cleaned_data
            options.orientation = data['orientation'].lower()
            options.size = data['cardsize'].lower()
            # due to argparse this should be a list of lists
            options.expansions = [[e] for e in data['expansions']]
            options.papersize = data['pagesize']
            options.cropmarks = data['cropmarks']
            options.wrapper = data['wrappers']
            options.count = data['counts']
            options.tab_name_align = data['tab_name_align']
            options.tab_side = data['tab_side']
            options.expansion_dividers = data['expansion_dividers']
            options.cost = data['cost_icon']
            options.set_icon = data['set_icon']
            options.order = data['order']
            options.special_card_groups = data['group_special']
            options.tabs_only = data['tabsonly']
            options.language = data['language']
            options.exclude_events = data['events']
            options.exclude_landmarks = data['events']
            options.text_front = data['divider_front_text']
            options.text_back = data['divider_back_text']
            options.no_page_footer = data['no_footer']
            options = domdiv.main.clean_opts(options)
            print 'options after cleaning:', options

            # Create the HttpResponse object with the appropriate PDF headers.
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="sumpfork_dominion_tabs.pdf"'
            options.outfile = response

            domdiv.main.generate(options)
            return response
    else:
        form = TabGenerationOptionsForm()

    return render(request, 'dominion_dividers/index.html', {'form': form})


# def chitbox(request):
#     if request.method == 'POST':
#         form = ChitBoxForm(request.POST, request.FILES)
#         if form.is_valid():
#             data = form.cleaned_data
#             # Create the HttpResponse object with the appropriate PDF headers.
#             response = HttpResponse(mimetype='application/pdf')
#             response['Content-Disposition'] = 'attachment; filename="sumpfork_chitbox.pdf"'
#             c = ChitBoxGenerator.fromRawData(
#                 data['width'], data['length'], data['height'], response, data['main_image'], data['side_image']
#             )
#             c.generate()

#             return response
#     else:
#         form = ChitBoxForm()
#     return render(request, 'domtabs/chitboxes.html', {'form': form})
