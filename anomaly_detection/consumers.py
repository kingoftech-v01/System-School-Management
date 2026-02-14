"""
WebSocket consumers for real-time anomaly alerts.
Direction/admin users receive live toast notifications when anomalies are detected.
"""

import json
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class AlertConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer that pushes anomaly alerts to connected staff users."""

    async def connect(self):
        user = self.scope.get('user')
        if user is None or user.is_anonymous:
            await self.close()
            return

        # Only allow staff / direction / admin users
        role = getattr(user, 'role', '')
        if not (user.is_staff or user.is_superuser or role in ('direction', 'admin', 'prefet')):
            await self.close()
            return

        # Join the alerts group (tenant-scoped if possible)
        tenant_id = getattr(user, 'tenant_id', None)
        if tenant_id:
            self.group_name = f'alerts_tenant_{tenant_id}'
        else:
            self.group_name = 'alerts_global'

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Also join global group so super-admins see everything
        if user.is_superuser:
            await self.channel_layer.group_add('alerts_global', self.channel_name)

        await self.accept()
        logger.info("WebSocket alert connection opened for user %s (group: %s)", user.pk, self.group_name)

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        user = self.scope.get('user')
        if user and not user.is_anonymous and user.is_superuser:
            await self.channel_layer.group_discard('alerts_global', self.channel_name)

    async def alert_notification(self, event):
        """Handler for alert.notification type messages from the channel layer."""
        await self.send_json(event['data'])
