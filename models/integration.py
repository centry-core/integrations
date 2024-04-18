from pylon.core.tools import log
from sqlalchemy import Integer, Column, String, Boolean, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSON
from uuid import uuid4

from tools import db_tools, db, rpc_tools
from ..models.pd.integration import IntegrationBase


class IntegrationAdmin(db_tools.AbstractBaseMixin, db.Base, rpc_tools.RpcMixin, rpc_tools.EventManagerMixin):
    __tablename__ = "integration"
    __table_args__ = (
        Index(
            'ix_default_uc',  # Index name
            'name',  # Columns which are part of the index
            unique=True,
            postgresql_where=Column('is_default')  # The condition
        ),
    )
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=False)
    settings = Column(JSON, unique=False, default={})
    is_default = Column(Boolean, default=False, nullable=False)
    section = Column(String(64), unique=False, nullable=False)
    config = Column(JSON, unique=False, default={})
    task_id = Column(String(256), unique=False, nullable=True)
    status = Column(String(256), unique=False, nullable=False, default='success')
    # ALTER TABLE "Project-1"."integration" ADD COLUMN uid VARCHAR(128)
    # ALTER TABLE "Project-1"."integration" ALTER COLUMN uid NOT NULL
    uid = Column(String(128), unique=True, nullable=False)

    def make_default(self, session):
        session.query(IntegrationAdmin).where(
            IntegrationAdmin.name == self.name,
            IntegrationAdmin.is_default == True,
            IntegrationAdmin.id != self.id
        ).update({IntegrationAdmin.is_default: False})
        self.is_default = True
        # session.add(self)
        # session.commit()

    def set_task_id(self, task_id: str):
        with db.get_session() as session:
            session.query(IntegrationAdmin).where(
                IntegrationAdmin.id == self.id
            ).update({IntegrationAdmin.task_id: task_id})
            session.commit()

    def insert(self, session):
        if not self.uid:
            self.uid = str(uuid4())
        if not session.query(IntegrationAdmin).filter(
                IntegrationAdmin.name == self.name,
                IntegrationAdmin.is_default == True,
        ).first():
            self.is_default = True
        session.add(self)
        session.commit()
        session.refresh(self)
        settings: dict = self.rpc.call.integrations_process_secrets(
            integration_data=IntegrationBase.from_orm(self).dict(),
        )
        session.query(IntegrationAdmin).where(
            IntegrationAdmin.id == self.id
        ).update({IntegrationAdmin.settings: settings})
        # session.commit()
        self.event_manager.fire_event(f'{self.name}_created_or_updated', self.to_json())



class IntegrationProject(db_tools.AbstractBaseMixin, db.Base, rpc_tools.RpcMixin, rpc_tools.EventManagerMixin):
    __tablename__ = "integration"
    __table_args__ = {'schema': 'tenant'}

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=False)
    project_id = Column(Integer, unique=False, nullable=True)
    settings = Column(JSON, unique=False, default={})
    is_default = Column(Boolean, default=False, nullable=False)
    section = Column(String(64), unique=False, nullable=False)
    config = Column(JSON, unique=False, default={})
    task_id = Column(String(256), unique=False, nullable=True)
    status = Column(String(256), unique=False, nullable=False, default='success')
    # ALTER TABLE "Project-1"."integration" ADD COLUMN uid VARCHAR(128)
    # ALTER TABLE "Project-1"."integration" ALTER COLUMN uid NOT NULL
    uid = Column(String(128), unique=True, nullable=False)

    def insert(self, session):
        if not self.uid:
            self.uid = str(uuid4())
        session.add(self)
        session.commit()
        inherited_integration = IntegrationAdmin.query.filter(
            IntegrationAdmin.name == self.name,
            IntegrationAdmin.config['is_shared'].astext.cast(Boolean) == True,
        ).first()
        default_integration = session.query(IntegrationDefault).filter(
            IntegrationDefault.name == self.name,
            IntegrationDefault.is_default == True,
        ).one_or_none()
        if not inherited_integration and not default_integration:
            self.rpc.call.integrations_make_default_integration(self, self.project_id)
        self.process_secret_fields(session)
        self.event_manager.fire_event(f'{self.name}_created_or_updated', self.to_json())

    def process_secret_fields(self, session):
        settings: dict = self.rpc.call.integrations_process_secrets(
            integration_data=IntegrationBase.from_orm(self).dict(),
        )
        session.query(IntegrationProject).filter(
            IntegrationProject.id == self.id
        ).update({IntegrationProject.settings: settings})
        session.commit()


class IntegrationDefault(db_tools.AbstractBaseMixin, db.Base, rpc_tools.RpcMixin, rpc_tools.EventManagerMixin):
    __tablename__ = "integration_default"
    __table_args__ = (
        Index(
            'ix_project_default_uc',  # Index name
            'name',  # Columns which are part of the index
            unique=True,
            postgresql_where=Column('is_default')  # The condition
        ),
        {'schema': 'tenant'}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=False)
    integration_id = Column(Integer, unique=False, nullable=False)
    project_id = Column(Integer, unique=False, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    section = Column(String(64), unique=False, nullable=False)
