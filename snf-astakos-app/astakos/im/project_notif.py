# Copyright 2013 GRNET S.A. All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
#   1. Redistributions of source code must retain the above
#      copyright notice, this list of conditions and the following
#      disclaimer.
#
#   2. Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials
#      provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY GRNET S.A. ``AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL GRNET S.A OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and
# documentation are those of the authors and should not be
# interpreted as representing official policies, either expressed
# or implied, of GRNET S.A.

import logging
from django.utils.translation import ugettext as _
from astakos.im import settings
from astakos.im.notifications import build_notification, NotificationError
from astakos.im import messages

logger = logging.getLogger(__name__)

MEM_CHANGE_NOTIF = {
    'subject':   _(messages.PROJECT_MEMBERSHIP_CHANGE_SUBJECT),
    'template': 'im/projects/project_membership_change_notification.txt',
}

MEM_ENROLL_NOTIF = {
    'subject':   _(messages.PROJECT_MEMBERSHIP_ENROLL_SUBJECT),
    'template': 'im/projects/project_membership_enroll_notification.txt',
}

SENDER = settings.SERVER_EMAIL
NOTIFY_RECIPIENTS = [e[1] for e in settings.MANAGERS + settings.HELPDESK]


def membership_change_notify(project, user, action):
    try:
        notification = build_notification(
            SENDER,
            [user.email],
            MEM_CHANGE_NOTIF['subject'] % project.__dict__,
            template=MEM_CHANGE_NOTIF['template'],
            dictionary={'object': project, 'action': action})
        notification.send()
    except NotificationError, e:
        logger.error(e.message)


def membership_enroll_notify(project, user):
    try:
        notification = build_notification(
            SENDER,
            [user.email],
            MEM_ENROLL_NOTIF['subject'] % project.__dict__,
            template=MEM_ENROLL_NOTIF['template'],
            dictionary={'object': project})
        notification.send()
    except NotificationError, e:
        logger.error(e.message)


def membership_request_notify(project, requested_user):
    try:
        notification = build_notification(
            SENDER,
            [project.application.owner.email],
            _(messages.PROJECT_MEMBERSHIP_REQUEST_SUBJECT) % project.__dict__,
            template='im/projects/project_membership_request_notification.txt',
            dictionary={'object': project, 'user': requested_user.email})
        notification.send()
    except NotificationError, e:
        logger.error(e.message)


def membership_leave_request_notify(project, requested_user):
    template = 'im/projects/project_membership_leave_request_notification.txt'
    try:
        notification = build_notification(
            SENDER,
            [project.application.owner.email],
            _(messages.PROJECT_MEMBERSHIP_LEAVE_REQUEST_SUBJECT) %
            project.__dict__,
            template=template,
            dictionary={'object': project, 'user': requested_user.email})
        notification.send()
    except NotificationError, e:
        logger.error(e.message)


def application_submit_notify(application):
    try:
        notification = build_notification(
            SENDER, NOTIFY_RECIPIENTS,
            _(messages.PROJECT_CREATION_SUBJECT) % application.__dict__,
            template='im/projects/project_creation_notification.txt',
            dictionary={'object': application})
        notification.send()
    except NotificationError, e:
        logger.error(e.message)


def application_deny_notify(application):
    try:
        notification = build_notification(
            SENDER,
            [application.owner.email],
            _(messages.PROJECT_DENIED_SUBJECT) % application.__dict__,
            template='im/projects/project_denial_notification.txt',
            dictionary={'object': application})
        notification.send()
    except NotificationError, e:
        logger.error(e.message)


def application_approve_notify(application):
    try:
        notification = build_notification(
            SENDER,
            [application.owner.email],
            _(messages.PROJECT_APPROVED_SUBJECT) % application.__dict__,
            template='im/projects/project_approval_notification.txt',
            dictionary={'object': application})
        notification.send()
    except NotificationError, e:
        logger.error(e.message)


def project_termination_notify(project):
    app = project.application
    try:
        build_notification(
            SENDER,
            [project.application.owner.email],
            _(messages.PROJECT_TERMINATION_SUBJECT) % app.__dict__,
            template='im/projects/project_termination_notification.txt',
            dictionary={'object': project}
        ).send()
    except NotificationError, e:
        logger.error(e.message)


def project_suspension_notify(project):
    try:
        build_notification(
            SENDER,
            [project.application.owner.email],
            _(messages.PROJECT_SUSPENSION_SUBJECT) % project.__dict__,
            template='im/projects/project_suspension_notification.txt',
            dictionary={'object': project}
        ).send()
    except NotificationError, e:
        logger.error(e.message)


def project_unsuspension_notify(project):
    try:
        build_notification(
            SENDER,
            [project.application.owner.email],
            _(messages.PROJECT_UNSUSPENSION_SUBJECT) % project.__dict__,
            template='im/projects/project_unsuspension_notification.txt',
            dictionary={'object': project}
        ).send()
    except NotificationError, e:
        logger.error(e.message)


def project_reinstatement_notify(project):
    try:
        build_notification(
            SENDER,
            [project.application.owner.email],
            _(messages.PROJECT_REINSTATEMENT_SUBJECT) % project.__dict__,
            template='im/projects/project_reinstatement_notification.txt',
            dictionary={'object': project}
        ).send()
    except NotificationError, e:
        logger.error(e.message)
