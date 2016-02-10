import requests

# Hard-Coding my URL and API key for now is a stopgap


BASE_URL = "https://n123.meraki.com/api/v0"
API_KEY = "X-Cisco-Meraki-API-Key"

JSON_KEY = "Content-Type"
JSON_VAL = "application/json"
HEADERS = {API_KEY: API_VAL, JSON_KEY: JSON_VAL}


def get_data(level="", request_string="", url_id="", ext_url=""):
    """ Defines a base get request to the Meraki Dashboard.
        One can be built using this function, or a pre-formatted one can be
        passed in.
        Args:
            level: A string of which level of data to query from; current valid
                top-level request types are organizations or networks.
            request_string: String indicating type of data to be queried; some
                requests such as determining Org access for a given API key do
                not require one.
            url_id: String containing an Org or Network ID.
            ext_url: an externally formatted URL.

        Returns:
            A requests.get object containing, among other things, the HTTP
            HTTP return code of the request, and the returned data.
    """
# TODO (Alex): Docstring needs some work here to build-out what different
# request strings indicate, and will need to work on adding exceptions.

    if ext_url:
        data = requests.get(ext_url, headers=HEADERS)
    else:
        url = "%s/%s/%s/%s/" % (BASE_URL.strip("/"), level.strip("/"),
                                url_id.strip("/"), request_string.strip("/"))
        data = requests.get(url, headers=HEADERS)
    return data

class AdminRequests(object):
    """ All methods, exceptions, and handlers to define, modify, or remove a
        Dashboard admin account.
    """
    def __init__(self):
        self.url = "%s/organizations/%s/admins" % (BASE_URL, ORG_ID)
        self.valid_access_keys = set(["tag", "access"])
        self.valid_access_vals = set(["full", "read-only", "none"])

    def _provided_access_valid(self, access):
        if access not in self.valid_access_vals:
            # TODO (Alex): Raise proper exception
            print "Invalid access type specified!"

    def _provided_tags_valid(self, tags):
        if not isinstance(tags, list):
            # TODO (Alex): raise exception properly here
            print "tags must be provided in a list!"

        for i in tags:
            if (not isinstance(i, dict)
                    or not self.valid_access_keys.issuperset(i.keys())
                    or not i["access"] in self.valid_access_vals):
                # TODO (Alex): raise exception properly here too
                # conditionals may have to be split out for
                # more verbose handling
                print "Incorrect format specified for tags!"

    def _admin_exists(self, admin_id):
        check = get_data(ext_url=self.url)
        for admin in check.json():
            if admin["email"] == admin_id or admin["id"] == admin_id:
                return admin

        return None


    def add_admin(self, name, email, access, tags=None):
        """ Define a new org-level Admin account on Dashboard under
            Organization -> Administrators
            Args:
                name: Name of the new admin.
                email: Email of the new admin.
                access: Their access level; currently only supports full
                    admins, read-only admins, or tag-based admins; not
                    network-level admins.
                tags: A list of dictionaries formatted as
                [{tag:tag-name}, {access:access-level}]; tags don't need to be
                prexisting on Dashboard.
            Returns:
                new_admin: a request object of the new admin's values
                as specified by the passed arguments and the HTTP
                return code for it, or None if the user already exists
        """

        exists = self._admin_exists(email)
        if exists:
            print "An account already exists for %s" % exists["email"]
            return None
        self._provided_access_valid(access)
        admin = {"name": name, "email": email, "orgAccess": access}
        if tags:
            self._provided_tags_valid(tags)
            admin["tags"] = tags

        new_admin = requests.post(self.url, json=admin, headers=HEADERS)

        # TODO (Alex): Right now this just returns regardless of whether
        # the request was successful or not; this will need defined handlers.
        return new_admin

    def update_admin(self, admin_id, to_update):
        """Update an existing admin's permissions or access.
        Args:
            admin_id: A user ID string or email address.
            to_update: a dict of the fields to be updated; valid keys are
            orgAccess, name, tags, and network.
        Returns:
            updated: The request object of the updated admin, or None if the
            passed admin ID doesn't exist.
        """

        valid_updates = set(["orgAccess", "name", "tag", "networks"])
        exists = self._admin_exists(admin_id)
        if not exists:
            print "No admin with ID %s; skipping." % admin_id
            return None
        elif not admin_id.isdigit():
            admin_id = exists["id"]
        if not isinstance(to_update, dict):
            # TODO (Alex): Error here
            pass
        elif not set(to_update.keys()).issubset(valid_updates):
            # TODO (Alex): Error here
            pass
        if to_update.has_key("tag"):
            self._provided_tags_valid(to_update["tag"])
        if to_update.has_key("orgAccess"):
            self._provided_access_valid()


    def del_admin(self, admin_id, skip_confirm=True):
        """ Delete a specified admin account.
            Args:
                admin_id: ID string of the admin to be deleted.
                no_confirm: Bool to prompt for confirmation before request is
                    submitted.
            Returns:
                deleted: The request object of the deleted admin, or None if the
                passed admin ID doesn't exist.
        """

        url = "%s/%s" % (self.url, admin_id)
        to_delete = self._admin_exists(admin_id)

        if not to_delete:
            print "No admin with ID %s; skipping." % admin_id
            return None

        elif not skip_confirm:
            prompt = ("Confirm deletion of user %s (%s) from organization %s "
                      "(y/n): ") % (to_delete["name"], to_delete["email"],
                                    ORG_ID)
            confirm = raw_input(prompt)
            if confirm.lower() == "n" or confirm.lower() == "no":
                print "Cancelling delete request\n"
                return None

        deleted = requests.delete(url, headers=HEADERS)
        return deleted


