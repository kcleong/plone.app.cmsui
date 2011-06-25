from datetime import datetime
from DateTime import DateTime

from Products.CMFCore.utils import getToolByName
from zope.publisher.browser import BrowserView
from plone.app.cmsui.interfaces import _

from zope.interface import Interface, implements
from zope import schema
from z3c.form import form, field, button
from zope.schema import vocabulary, interfaces
from z3c.form.browser.radio import RadioFieldWidget

class WorkflowActionsSourceBinder(object):
    implements(interfaces.IContextSourceBinder)
    """Generates vocabulary for all allowed workflow transitions"""
    
    def __call__(self, context):
        wft = getToolByName(context, 'portal_workflow')
        return vocabulary.SimpleVocabulary([
            vocabulary.SimpleVocabulary.createTerm(t['id'],t['id'],t['title'])
            for t in wft.getTransitionsFor(context)
        ])

class IWorkflowPanel(Interface):
    """Form for workflow panel"""
    workflow_action = schema.Choice(
        title = _(u'label_workflow_action', u"Change State"),
        description = _(u'help_workflow_action', 
                          default=u"Select the transition to be used for modifying the items state."),
        source= WorkflowActionsSourceBinder(),
        required= False,
        )
    comment = schema.Text(
        title = _(u"label_comment", u"Comments"),
        description = _(u'help_comment',
                          default=u"Will be added to the publishing history. If multiple "
                                   "items are selected, this comment will be attached to all of them."),
        required= False,
        )
    effective_date = schema.Datetime(
        title = _(u'label_effective_date', u'Publishing Date'),
        description = _(u'help_effective_date',
                          default=u"If this date is in the future, the content will "
                                   "not show up in listings and searches until this date."),
        required = False
        )
    expiration_date = schema.Datetime(
        title = _(u'label_expiration_date', u'Expiration Date'),
        description = _(u'help_expiration_date',
                              default=u"When this date is reached, the content will no"
                                       "longer be visible in listings and searches."),
        required = False
        )

class WorkflowPanel(form.Form):
    """Shows a panel with the adanced workflow options
    """
    fields = field.Fields(IWorkflowPanel)
    fields['workflow_action'].widgetFactory = RadioFieldWidget
    ignoreContext = True

    @button.buttonAndHandler(u'Save')
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        
        workflow_action = data.get('workflow_action', '')
        effective_date = data.get('effective_date', None)
        if workflow_action and not effective_date and self.context.EffectiveDate()=='None':
            effective_date=DateTime()
        expiration_date = data.get('expiration_date', None)
        
        self._editContent(self.context, effective_date, expiration_date)
        
        if workflow_action is not None:
            self.context.portal_workflow.doActionFor(self.context, workflow_action, comment=data.get('comment', ''))
            return "Complete"
        self.request.response.redirect(self.context.absolute_url())

    @button.buttonAndHandler(u'Cancel')
    def cancel(self, action):
        self.request.response.redirect(self.context.absolute_url())

    def _editContent(self, context, effective, expiry):
        kwargs = {}
        if isinstance(effective, datetime):
            kwargs['effective_date'] = DateTime(effective)
        elif effective and (isinstance(effective, DateTime) or len(effective) > 5): # may contain the year
            kwargs['effective_date'] = effective
        if isinstance(expiry, datetime):
            kwargs['expiration_date'] = DateTime(expiry)
        elif expiry and (isinstance(expiry, DateTime) or len(expiry) > 5): # may contain the year
            kwargs['expiration_date'] = expiry
        context.plone_utils.contentEdit(context, **kwargs)
