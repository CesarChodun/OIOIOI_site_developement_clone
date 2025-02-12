import socket

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class IpDnsBackend(ModelBackend):
    """Authenticates users by their ip or dns hostname.

       This backend checks given arguments against models
       :class:'IpToUser' and :class:'DnsToUser' (in this order).
       When dns_name is not given, then it tries to call
       reverse-dns service on ip_addr.
    """
    description = _("IP/DNS based authentication")
    supports_authentication = True

    def authenticate(self, dns_name=None, ip_addr=None):
        if ip_addr:
            try:
                return User.objects.get(iptouser__ip_addr=ip_addr)
            except User.DoesNotExist:
                pass

        hostname = dns_name or self._resolve_hostname(ip_addr)
        if hostname:
            try:
                return User.objects.get(dnstouser__dns_name=hostname)
            except User.DoesNotExist:
                pass

        return None

    def _resolve_hostname(self, ip):
        if ip:
            try:
                return socket.gethostbyaddr(ip)[0]
            except socket.herror:
                pass

        return None
