from typing import Set

from bpy.types import Context, Panel

from . import (
    GameFileImporterOperator,
    GameFileImporterOperatorProps,
    ImporterOperatorProps,
    MaterialToggleOperatorProps,
    ModelImporterOperatorProps,
)
from ..asset import AssetCallbacks
from ..plumber import Importer


class ImportMdl(
    GameFileImporterOperator,
    ImporterOperatorProps,
    GameFileImporterOperatorProps,
    ModelImporterOperatorProps,
    MaterialToggleOperatorProps,
):
    """Import Source Engine MDL model"""

    bl_idname = "import_scene.plumber_mdl"
    bl_label = "Import MDL"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> Set[str]:
        fs = self.get_game_fs(context)

        try:
            importer = Importer(
                fs,
                AssetCallbacks(context),
                self.get_threads_suggestion(context),
                target_fps=self.get_target_fps(context),
                simple_materials=self.simple_materials,
                allow_culling=self.allow_culling,
                editor_materials=self.editor_materials,
                texture_interpolation=self.texture_interpolation,
            )
        except OSError as err:
            self.report({"ERROR"}, f"could not open file system: {err}")
            return {"CANCELLED"}

        try:
            importer.import_mdl(
                self.filepath,
                self.from_game_fs,
                import_materials=self.import_materials,
                import_animations=self.import_animations,
            )
        except OSError as err:
            self.report({"ERROR"}, f"could not import mdl: {err}")
            return {"CANCELLED"}

        return {"FINISHED"}

    def draw(self, context: Context):
        if self.from_game_fs:
            ModelImporterOperatorProps.draw_props(self.layout, self, context)
            MaterialToggleOperatorProps.draw_props(self.layout, self, context)


class PLUMBER_PT_mdl_main(Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        operator = context.space_data.active_operator
        return operator.bl_idname == "IMPORT_SCENE_OT_plumber_mdl"

    def draw(self, context: Context) -> None:
        ModelImporterOperatorProps.draw_props(
            self.layout, context.space_data.active_operator, context
        )
