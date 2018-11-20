from django.contrib.admin.widgets import AdminTimeWidget, AdminDateWidget
from django.forms import TextInput, Select, Textarea
from django import forms


class HTML5Input(TextInput):
    def __init__(self, attrs=None, input_type=None):
        self.input_type = input_type
        super(HTML5Input, self).__init__(attrs)


class LinkedSelect(Select):
    """
    Linked select - Adds link to foreign item, when used with foreign key field
    """

    def __init__(self, attrs=None, choices=()):
        attrs = _make_attrs(attrs, classes="linked-select")
        super(LinkedSelect, self).__init__(attrs, choices)


class EnclosedInput(TextInput):
    """
    Widget for bootstrap appended/prepended inputs
    """

    def __init__(self, attrs=None, prepend=None, append=None):
        """
        For prepend, append parameters use string like %, $ or html
        """
        self.prepend = prepend
        self.append = append
        super(EnclosedInput, self).__init__(attrs=attrs)

    def enclose_value(self, value):
        """
        If value doesn't starts with html open sign "<", enclose in add-on tag
        """
        if value.startswith("<"):
            return value
        if value.startswith("icon-"):
            value = '<i class="%s"></i>' % value
        return '<span class="add-on">%s</span>' % value

    def render(self, name, value, attrs=None):
        output = super(EnclosedInput, self).render(name, value, attrs)
        div_classes = []
        if self.prepend:
            div_classes.append('input-prepend')
            self.prepend = self.enclose_value(self.prepend)
            output = ''.join((self.prepend, output))
        if self.append:
            div_classes.append('input-append')
            self.append = self.enclose_value(self.append)
            output = ''.join((output, self.append))

        return mark_safe(
            '<div class="%s">%s</div>' % (' '.join(div_classes), output))


class AutosizedTextarea(Textarea):
    """
    Autosized Textarea - textarea height dynamically grows based on user input
    """

    def __init__(self, attrs=None):
        new_attrs = _make_attrs(attrs, {"rows": 2}, "autosize")
        super(AutosizedTextarea, self).__init__(new_attrs)

    @property
    def media(self):
        return forms.Media(js=[static("widget/js/jquery.autosize-min.js")])

    def render(self, name, value, attrs=None):
        output = super(AutosizedTextarea, self).render(name, value, attrs)
        output += mark_safe(
            "<script type=\"text/javascript\">Suit.$('#id_%s').autosize();</script>"
            % name)
        return output


class SuitDateWidget(AdminDateWidget):
    def __init__(self, attrs=None, format=None):
        defaults = {'placeholder': _('Date:')[:-1]}
        new_attrs = _make_attrs(attrs, defaults, "vDateField input-small")
        super(SuitDateWidget, self).__init__(attrs=new_attrs, format=format)

    def render(self, name, value, attrs=None):
        output = super(SuitDateWidget, self).render(name, value, attrs)
        return mark_safe(
            '<div class="input-append suit-date">%s<span '
            'class="add-on"><i class="icon-calendar"></i></span></div>' %
            output)


class SuitTimeWidget(AdminTimeWidget):
    def __init__(self, attrs=None, format=None):
        defaults = {'placeholder': _('Time:')[:-1]}
        new_attrs = _make_attrs(attrs, defaults, "vTimeField input-small")
        super(SuitTimeWidget, self).__init__(attrs=new_attrs, format=format)

    def render(self, name, value, attrs=None):
        output = super(SuitTimeWidget, self).render(name, value, attrs)
        return mark_safe(
            '<div class="input-append suit-date suit-time">%s<span '
            'class="add-on"><i class="icon-time"></i></span></div>' %
            output)


class SuitSplitDateTimeWidget(forms.SplitDateTimeWidget):
    """
    A SplitDateTime Widget that has some admin-specific styling.
    """

    def __init__(self, attrs=None):
        widgets = [SuitDateWidget, SuitTimeWidget]
        forms.MultiWidget.__init__(self, widgets, attrs)

    def format_output(self, rendered_widgets):
        out_tpl = '<div class="datetime">%s %s</div>'
        return mark_safe(out_tpl % (rendered_widgets[0], rendered_widgets[1]))


def _make_attrs(attrs, defaults=None, classes=None):
    result = defaults.copy() if defaults else {}
    if attrs:
        result.update(attrs)
    if classes:
        result["class"] = " ".join((classes, result.get("class", "")))
    return result


import copy
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms import Widget
from django.utils.datastructures import MultiValueDict, MergeDict
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from django.utils.translation import ugettext as _
from django.contrib.admin.templatetags.admin_static import static


class MultipleTreeSelect(Widget):
    allow_multiple_selected = True

    def __init__(self, attrs=None, q=Q(), add_link=None):
        self.q = q
        self.add_link = add_link
        if add_link is None:
            raise Exception("add_link parameter must be set.")
        super(MultipleTreeSelect, self).__init__(attrs)

    def value_from_datadict(self, data, files, name):
        if isinstance(data, (MultiValueDict, MergeDict)):
            return data.getlist(name)
        return data.get(name, None)

    def render(self, name, value, attrs=None, choices=()):
        self.model = self.choices.field._queryset.model
        if attrs is None:
            attrs = {}
            #attrs['style'] = 'height: 130px; width:150px;'
        attrs['name'] = name
        attrs['id'] = name + '_%s'
        attrs['class'] = 'class_' + name

        final_attrs = self.build_attrs(**attrs)
        field = '<div style="display:inline-block; margin-right:2px" class="tree-select"><div><a href="' + reverse(
            'admin:%s_%s_add' % self.add_link) + '%s" class="add-another" id="' + (
                    'add_%s_' % name) + '%s" onclick="return showAddAnotherPopup(this);">' + \
                '<img src="%s" width="10" height="10" alt="%s"/></a></div>' % (
                    static('admin/img/icon_addlink.gif'), _('Add Another'))

        fullfield = field + format_html('<select size="3" {0}>', flatatt(final_attrs))

        js = '''
         <script type="text/javascript">
        function sprintf(format, etc) {
            var arg = arguments;
            var i = 1;
            return format.replace(/%((%)|s)/g, function (m) { return m[2] || arg[i++] })
        }
         django.jQuery(document).on('change', '.''' + attrs['class'] + '''', function(e) {
           django.jQuery.getJSON("''' + reverse('admin:%s_%s_%s' % (self.add_link + ('fetch',))) + '''/?parent="+this.value, function(data) {
                var par = django.jQuery(e.currentTarget).parents('.tree-select');
                par.nextAll('.tree-select').remove();
                if(data.length==0) return;
                e.target.name = e.target.name.replace(/\[\]$/, '')+'_dump';
                str = \'''' + fullfield + '''\';
                for(var i=0; i<data.length; i++) {
                    str += '<option value="'+data[i].id+'">'+data[i].name+'</option>'
                }
                str += '</select></div>';
                var index = par.index();
                str = sprintf(str, '', index+1, index+1);
                var add = par.after(str).parent().find('.tree-select:last .add-another');
                add.attr('href', add.attr('href')+'?parent='+e.currentTarget.options[e.currentTarget.selectedIndex].value);
           });
         });
         </script>
        '''

        base_choices = self.model.objects.filter(self.q & Q(level=0)).values_list("id", "name")

        sha = [fullfield % ('', 1, 1)]
        options = self.render_options(value, base_choices)
        sha.append(options)
        sha.append('</select></div>')
        initial = '<div class="treeField">' + mark_safe('\n'.join(sha))

        if value is None or value == []:
            str = initial + '</div>' + js
        else:
            values = value if isinstance(value, list) else [value]
            str = []
            final_attrs = self.build_attrs(**(dict(attrs.items() + {'name': '%s'}.items())))
            for value in values:
                base_cat = self.model.objects.get(pk=value).get_ancestors(include_self=True)
                out = ""
                for i, item in enumerate(base_cat):
                    q = [field + format_html('<select size="3" {0}>', flatatt(final_attrs))]
                    options = self.render_options(item.id, [(item.id, item.name)]) if i > 0 else self.render_options(
                        base_cat[0].id, base_choices)
                    q.append(options)
                    q.append('</select></div>')
                    out += mark_safe('\n'.join(q) % (
                        '?parent=%s' % base_cat[i - 1].id if i > 0 else '', i, i,
                        name if i + 1 == len(base_cat) else ''))
                str.append(
                    '<div class="treeField">' + out + '''<span class="deleteRow" onclick="$(this).closest('.treeField').remove()">delete</span></div>''')
            str = "\n".join(str) + js

        str += '''<div><div class="little_button add_one_more" onclick="$(this).closest('.field').find('.treeField:last').after($(this).find('script').html())">%s<script type="template">%s</script></div>''' % (
            _('add'),
            initial + '''<span class="deleteRow" onclick="$(this).closest('.treeField').remove()">delete</span></div>''',)
        return str


    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_text(option_value)
        selected_choices = [str(x) for x in selected_choices]
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        return format_html(u'<option value="{0}"{1}>{2}</option>',
                           option_value,
                           selected_html,
                           force_text(option_label))

    def render_options(self, value, choices):
        output = []
        for option_value, option_label in choices:
            if isinstance(option_label, (list, tuple)):
                output.append(format_html('<optgroup label="{0}">', force_text(option_value)))
                for option in option_label:
                    output.append(self.render_option([value], *option))
                output.append('</optgroup>')
            else:
                output.append(self.render_option([value], option_value, option_label))
        return '\n'.join(output)

    def get_choices(self, type, level, value):
        return self.model.objects.filter(self.q & Q(level=level)).values_list("id", "name"), str(value)


class TreeSelect(Widget):
    allow_multiple_selected = False

    def __init__(self, attrs=None, q=Q(), proxy_model=True, max_depth=0, add_link=None):
        self.q = q
        self.proxy_model = proxy_model
        self.max_depth = max_depth
        self.add_link = add_link
        if add_link is None:
            raise Exception("add_link parameter must be set.")
        super(TreeSelect, self).__init__(attrs)

    def render(self, name, value, attrs=None, choices=()):
        self.model = self.choices.field._queryset.model
        if not self.proxy_model:
            self.model = self.model.__bases__[0]
        if attrs is None:
            attrs = {}
            #attrs['style'] = 'height: 130px; width:150px;'
        attrs['name'] = name if isinstance(value, list) else name
        attrs['id'] = name + '_%s'
        attrs['class'] = 'class_' + name

        final_attrs = self.build_attrs(**attrs)
        output = ['<div style="display:inline-block; margin-right:2px" class="tree-select"><div><a href="' + reverse(
            'admin:%s_%s_add' % self.add_link) + '%s" class="add-another" id="' + (
                      'add_%s' % name) + '_%s" onclick="return showAddAnotherPopup(this);">' +
                  ('<img src="%s" width="10" height="10" alt="%s"/></a></div>' % (
                      static('admin/img/icon_addlink.gif'), _('Add Another'))) +
                  format_html('<select size="3" {0}>', flatatt(final_attrs))]

        js = '''
         <script type="text/javascript">
        function sprintf(format, etc) {
            var arg = arguments;
            var i = 1;
            return format.replace(/%((%)|s)/g, function (m) { return m[2] || arg[i++] })
        }'''
        js += '''
        var depth = %s;
        django.jQuery(document).on('change', '.%s', function(e) {
            console.log(e);
           var par = django.jQuery(e.currentTarget).parents('.tree-select');
           if (depth > 0 && par.prevAll('.tree-select').length+2 > depth)
                return par.addClass('end_tree');
           django.jQuery.getJSON("%s/?parent="+this.value, function(data) {
                par.nextAll('.tree-select').remove();
                if(data.length==0) return;
                e.target.name = e.target.name.replace(/\[\]$/, '')+'_dump';
                str = \'%s\';
                for(var i=0; i<data.length; i++) {
                    str += '<option value="'+data[i].id+'">'+data[i].name+'</option>'
                }
                str += '</select></div>';
                var index = par.index();
                str = sprintf(str, '', index+1, index+1);
                var add = par.after(str).parent().find('.tree-select:last .add-another');
                add.attr('href', add.attr('href')+'?parent='+e.currentTarget.options[e.currentTarget.selectedIndex].value);
           });
         });
         </script>
        ''' % (
            self.max_depth, attrs['class'], reverse('admin:%s_%s_%s' % (self.add_link[0], self.add_link[1], "fetch")),
            output[0])

        base_choices = self.model.objects.filter(self.q & Q(level=0)).values_list("id", "name")

        sha = [output[0] % ('', 1, 1)]
        options = self.render_options(value, base_choices)
        sha.append(options)
        sha.append('</select></div>' + js)
        initial = mark_safe('\n'.join(sha))

        if value is None:
            str = initial
        else:
            base_cat = self.model.objects.get(pk=value).get_ancestors(include_self=True)
            out = ""
            for i, item in enumerate(base_cat):
                q = copy.copy(output)
                options = self.render_options(item.id, [(item.id, item.name)]) if i > 0 else self.render_options(
                    base_cat[0].id, base_choices)
                q.append(options)
                q.append('</select></div>')
                out += mark_safe('\n'.join(q) % ('?parent=%s' % base_cat[i - 1].id if i > 0 else '', i, i))
            str = out + js

        str = '<div class="treeField">' + str + '</div>'
        if isinstance(value, list):
            str += '''<div><div class="little_button add_one_more" onclick="$(this).parent().siblings('.treeField').append($(this).find('script').html())">%s<script type="template">%s</script></div></div>''' % (
                _('add'), '<div class="treeField">' + initial + '</div>',)
        return str


    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_text(option_value)
        selected_choices = [str(x) for x in selected_choices]
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        return format_html(u'<option value="{0}"{1}>{2}</option>',
                           option_value,
                           selected_html,
                           force_text(option_label))

    def render_options(self, value, choices):
        output = []
        for option_value, option_label in choices:
            if isinstance(option_label, (list, tuple)):
                output.append(format_html('<optgroup label="{0}">', force_text(option_value)))
                for option in option_label:
                    output.append(self.render_option([value], *option))
                output.append('</optgroup>')
            else:
                output.append(self.render_option([value], option_value, option_label))
        return '\n'.join(output)

    def get_choices(self, type, level, value):
        base_cat = self.model.objects.get(pk=value)
        return self.model.objects.filter(self.q & Q(level=level)).values_list("id", "name"), str(value)

