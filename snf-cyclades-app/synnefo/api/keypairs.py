# Copyright (C) 2010-2016 GRNET S.A.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json

from django.conf.urls import patterns
from django.http import HttpResponse, HttpResponseServerError

from snf_django.lib import api
from snf_django.lib.api import utils, faults

from synnefo.userdata.models import PublicKeyPair
from synnefo.userdata.util import generate_keypair, SUPPORT_GENERATE_KEYS
from synnefo.api import util
from synnefo.db import transaction

from logging import getLogger

log = getLogger(__name__)

urlpatterns = patterns(
    'synnefo.api.keypairs',
    (r'^(?:/|.json|.xml)?$', 'demux'),
    (r'^/([\w-]+)(?:/|.json|.xml)?$', 'keypair_demux'),
)


def keypair_to_dict(keypair, details=False):
    """Given a PublicKeyPair object it returns a dict with the info stored in
    in the object.
    """
    d = {
        'name': keypair.name,
        'fingerprint': keypair.fingerprint,
        'public_key': keypair.content
    }
    if details is True:
        d['deleted'] = keypair.deleted
        d['id'] = keypair.id
        d['created_at'] = keypair.created_at.isoformat()
        d['deleted_at'] = None
        if keypair.deleted_at is not None:
            d['deleted_at'] = keypair.deleted_at.isoformat()
        d['updated_at'] = None
        if keypair.updated_at is not None:
            d['updated_at'] = keypair.updated_at.isoformat()
    return {'keypair': d}


def demux(request):
    if request.method == 'GET':
        return list_keypairs(request)
    elif request.method == 'POST':
        return create_new_keypair(request)
    else:
        return api.api_method_not_allowed(request,
                                          allowed_methods=['GET', 'POST'])


def keypair_demux(request, keypair_name):
    if request.method == 'GET':
        return get_keypair(request, keypair_name)
    if request.method == 'DELETE':
        return delete_keypair(request, keypair_name)
    else:
        return api.api_method_not_allowed(request,
                                          allowed_methods=['GET', 'DELETE'])


@api.api_method(http_method='GET', user_required=True, logger=log)
def list_keypairs(request):
    """List keypairs that are associated with this user.

    Normal response codes: 200

    Error response codes: unauthorized(401), forbidden(403)
    """
    active_keypairs = \
        PublicKeyPair.objects.filter(user=request.user_uniq).all()
    keypairs = [keypair_to_dict(keypair) for keypair in
                active_keypairs.order_by('name')]
    data = json.dumps({'keypairs': keypairs})
    return HttpResponse(data, status=200)


@api.api_method(http_method='POST', user_required=True, logger=log)
@transaction.commit_on_success
def create_new_keypair(request):
    """Generates or imports a keypair.

    Normal response code: 201

    Error response codes: badRequest(400), unauthorized(401), forbidden(403),
                          conflict(409)
    """

    if PublicKeyPair.user_limit_exceeded(request.user_uniq):
        return HttpResponseServerError("SSH keys limit exceeded")

    req = utils.get_json_body(request)
    try:
        keypair = req['keypair']
        assert(isinstance(req, dict))
        name = keypair['name']
    except (KeyError, AssertionError):
        raise faults.BadRequest('Malformed request.')

    try:
        # If the public_key is provided  and the corresponding
        # keypair already exists update the public key
        keypair_obj = util.get_keypair(name, request.user_uniq,
                                       for_update=True)
    except faults.ItemNotFound:
        keypair_obj = PublicKeyPair(name=name, user=request.user_uniq)

    new_keypair = None
    try:
        public_key = keypair['public_key']
        keypair_obj.content = public_key
    except KeyError:
        # If the public_key field is omitted, generate a new
        # keypair and return both the private and the public key
        if not SUPPORT_GENERATE_KEYS:
            raise faults.Forbidden(
                "Application does not support ssh keys generation")

        new_keypair = generate_keypair()
        keypair_obj.content = new_keypair['public']

    keypair_obj.save()

    data = keypair_to_dict(keypair_obj)
    if new_keypair is not None:
        data['keypair']['private_key'] = new_keypair['private']

    return HttpResponse(json.dumps(data), status=201)


@api.api_method(http_method='GET', user_required=True, logger=log)
def get_keypair(request, keypair_name):
    """Shows details for a keypair that is associated with the account.

    Normal response codes: 200

    Error response codes: unauthorized(401), forbidden(403), itemNotFound(404)
    """
    keypair = util.get_keypair(keypair_name, request.user_uniq)
    keypairdict = keypair_to_dict(keypair, details=True)
    data = json.dumps(keypairdict)
    return HttpResponse(data, status=200)


@api.api_method(http_method='DELETE', user_required=True, logger=log)
@transaction.commit_on_success
def delete_keypair(request, keypair_name):
    """Deletes a keypair.

    Normal response codes: 204

    Error response codes: unauthorized(401), forbidden(403), itemNotFound(404)

    NOTE: In version 2.10 Openstack added a new optional user_id field in the
          request to allow administrative users to upload keys for other users
          than themselves. This is not implemented by us.
    """
    keypair = util.get_keypair(keypair_name, request.user_uniq,
                               for_update=True)
    # The Keypair object should be deleted from the database
    keypair.delete()
    return HttpResponse(status=204)
