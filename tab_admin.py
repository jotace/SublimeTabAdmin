import sublime
import sublime_plugin
import os
import datetime


# ============================================================
# TAB ADMIN PARA SUBLIME TEXT 3
# ============================================================
#
# Administra las pestañas que todavía NO han sido guardadas
# como archivos físicos.
#
# Una pestaña sin guardar se identifica mediante:
#
#     view.file_name() is None
#
# Funciones:
#
# 1. Listar todas las pestañas sin guardar.
# 2. Mostrar una vista previa de su contenido.
# 3. Saltar directamente a una pestaña seleccionada.
# 4. Crear un respaldo de todas las pestañas sin guardar.
# 5. Cerrar solamente pestañas vacías y no modificadas.
# 6. Cerrar todas las pestañas sin guardar.
# 7. Alertas automáticas configurables.
#
# ============================================================


# ============================================================
# CONFIGURACIÓN DEL PLUGIN
# ============================================================

SETTINGS_FILE = "TabAdmin.sublime-settings"


def get_tab_admin_settings():
    """
    Carga la configuración de TabAdmin.
    """

    return sublime.load_settings(
        SETTINGS_FILE
    )


def get_setting_integer(
    setting_name,
    default_value
):
    """
    Obtiene una configuración numérica.

    Si el valor no existe o no es válido,
    devuelve el valor por defecto.
    """

    settings = get_tab_admin_settings()

    value = settings.get(
        setting_name,
        default_value
    )

    try:
        value = int(value)

    except Exception:
        value = default_value

    return value


def alerts_are_enabled():
    """
    Indica si las alertas automáticas están activadas.
    """

    settings = get_tab_admin_settings()

    return settings.get(
        "alerts_enabled",
        True
    )


# ============================================================
# FUNCIONES GENERALES
# ============================================================


# ------------------------------------------------------------
# COMPROBAR SI UNA VISTA ES UN BUFFER SIN GUARDAR
# ------------------------------------------------------------

def is_unsaved_view(view):
    """
    Devuelve True si la pestaña todavía no tiene
    un archivo físico asociado.
    """

    if view.file_name() is None:
        return True

    return False


# ------------------------------------------------------------
# OBTENER TODAS LAS PESTAÑAS SIN GUARDAR
# ------------------------------------------------------------

def get_unsaved_views(window):
    """
    Devuelve todas las pestañas de la ventana actual
    que todavía no han sido guardadas como archivo.
    """

    unsaved_views = []

    all_views = window.views()

    for view in all_views:

        if is_unsaved_view(view):
            unsaved_views.append(view)

    return unsaved_views


# ------------------------------------------------------------
# OBTENER NOMBRE VISIBLE DE LA PESTAÑA
# ------------------------------------------------------------

def get_view_title(view):
    """
    Obtiene el nombre visible de una pestaña.

    Si no existe nombre, devuelve "Untitled".
    """

    title = view.name()

    if title is None:
        return "Untitled"

    title = title.strip()

    if title == "":
        return "Untitled"

    return title


# ------------------------------------------------------------
# OBTENER ESTADO DE MODIFICACIÓN
# ------------------------------------------------------------

def get_view_status(view):
    """
    Indica si Sublime considera que la pestaña
    tiene modificaciones.
    """

    if view.is_dirty():
        return "MODIFICADA"

    return "sin cambios"


# ------------------------------------------------------------
# OBTENER VISTA PREVIA
# ------------------------------------------------------------

def get_preview_text(
    view,
    limit=180
):
    """
    Devuelve una vista previa del contenido.
    """

    size = view.size()

    if size == 0:
        return "(pestaña vacía)"

    end_position = min(
        size,
        limit
    )

    region = sublime.Region(
        0,
        end_position
    )

    text = view.substr(
        region
    )

    text = text.replace(
        "\r\n",
        " "
    )

    text = text.replace(
        "\n",
        " "
    )

    text = text.replace(
        "\r",
        " "
    )

    text = text.replace(
        "\t",
        " "
    )

    text = text.strip()

    if text == "":
        return "(sin contenido visible)"

    if size > limit:
        text = text + "..."

    return text


# ------------------------------------------------------------
# OBTENER CONTENIDO COMPLETO
# ------------------------------------------------------------

def get_full_view_content(view):
    """
    Devuelve el contenido completo de una pestaña.
    """

    size = view.size()

    region = sublime.Region(
        0,
        size
    )

    return view.substr(
        region
    )


# ------------------------------------------------------------
# DIRECTORIO PARA RESPALDOS
# ------------------------------------------------------------

def get_backup_directory():
    """
    Busca un directorio apropiado para los respaldos.

    Orden:

    1. ~/Desktop
    2. ~/Escritorio
    3. Packages/User/TabAdmin_Backups
    """

    home_directory = os.path.expanduser(
        "~"
    )

    # --------------------------------------------------------
    # Desktop
    # --------------------------------------------------------

    desktop_directory = os.path.join(
        home_directory,
        "Desktop"
    )

    if os.path.isdir(desktop_directory):
        return desktop_directory

    # --------------------------------------------------------
    # Escritorio
    # --------------------------------------------------------

    desktop_directory = os.path.join(
        home_directory,
        "Escritorio"
    )

    if os.path.isdir(desktop_directory):
        return desktop_directory

    # --------------------------------------------------------
    # Directorio alternativo
    # --------------------------------------------------------

    backup_directory = os.path.join(
        sublime.packages_path(),
        "User",
        "TabAdmin_Backups"
    )

    if not os.path.isdir(
        backup_directory
    ):

        os.makedirs(
            backup_directory
        )

    return backup_directory


# ============================================================
# COMANDO 1
#
# LISTAR PESTAÑAS SIN GUARDAR
# ============================================================

class ListUnsavedTabsCommand(
    sublime_plugin.WindowCommand
):

    def run(self):

        self.unsaved_views = get_unsaved_views(
            self.window
        )

        number_of_views = len(
            self.unsaved_views
        )

        if number_of_views == 0:

            sublime.message_dialog(
                "No hay pestañas sin guardar "
                "en esta ventana."
            )

            return

        items = []

        position = 1

        for view in self.unsaved_views:

            title = get_view_title(
                view
            )

            status = get_view_status(
                view
            )

            size = view.size()

            preview = get_preview_text(
                view
            )

            description = (
                "{}. {} | {} caracteres | {}"
            ).format(
                position,
                title,
                size,
                status
            )

            item = [
                description,
                preview
            ]

            items.append(
                item
            )

            position = position + 1

        self.window.show_quick_panel(
            items,
            self.on_select
        )


    def on_select(
        self,
        index
    ):

        # El usuario canceló.
        if index == -1:
            return

        number_of_views = len(
            self.unsaved_views
        )

        if index >= number_of_views:
            return

        selected_view = self.unsaved_views[
            index
        ]

        self.window.focus_view(
            selected_view
        )


# ============================================================
# COMANDO 2
#
# RESPALDAR TODAS LAS PESTAÑAS SIN GUARDAR
# ============================================================

class BackupUnsavedTabsCommand(
    sublime_plugin.WindowCommand
):

    def run(self):

        unsaved_views = get_unsaved_views(
            self.window
        )

        number_of_views = len(
            unsaved_views
        )

        if number_of_views == 0:

            sublime.message_dialog(
                "No hay pestañas sin guardar "
                "para respaldar."
            )

            return

        # ----------------------------------------------------
        # Fecha y hora
        # ----------------------------------------------------

        current_time = datetime.datetime.now()

        timestamp = current_time.strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        # ----------------------------------------------------
        # Archivo de respaldo
        # ----------------------------------------------------

        backup_directory = get_backup_directory()

        filename = (
            "sublime_unsaved_backup_{}.txt"
        ).format(
            timestamp
        )

        output_file = os.path.join(
            backup_directory,
            filename
        )

        # ----------------------------------------------------
        # Crear contenido
        # ----------------------------------------------------

        content = []

        content.append(
            "RESPALDO DE PESTAÑAS SIN GUARDAR"
        )

        content.append(
            "=" * 78
        )

        content.append("")

        content.append(
            "Fecha: {}".format(
                timestamp
            )
        )

        content.append(
            "Cantidad de pestañas: {}".format(
                number_of_views
            )
        )

        content.append("")
        content.append("=" * 78)
        content.append("")

        position = 1

        for view in unsaved_views:

            title = get_view_title(
                view
            )

            status = get_view_status(
                view
            )

            size = view.size()

            text = get_full_view_content(
                view
            )

            content.append(
                "PESTAÑA SIN GUARDAR {}".format(
                    position
                )
            )

            content.append(
                "-" * 78
            )

            content.append(
                "Título visible: {}".format(
                    title
                )
            )

            content.append(
                "Caracteres: {}".format(
                    size
                )
            )

            content.append(
                "Estado: {}".format(
                    status
                )
            )

            content.append("")

            content.append(
                "CONTENIDO:"
            )

            content.append(
                "-" * 78
            )

            content.append(
                text
            )

            content.append("")
            content.append("")
            content.append("=" * 78)
            content.append("")

            position = position + 1

        final_content = "\n".join(
            content
        )

        # ----------------------------------------------------
        # Guardar
        # ----------------------------------------------------

        try:

            with open(
                output_file,
                "w",
                encoding="utf-8"
            ) as backup_file:

                backup_file.write(
                    final_content
                )

        except Exception as error:

            error_message = (
                "No se pudo crear el respaldo.\n\n"
                "Error:\n{}"
            ).format(
                str(error)
            )

            sublime.error_message(
                error_message
            )

            return

        # ----------------------------------------------------
        # Confirmación
        # ----------------------------------------------------

        message = (
            "Respaldo creado correctamente.\n\n"
            "Pestañas respaldadas: {}\n\n"
            "Archivo:\n{}"
        ).format(
            number_of_views,
            output_file
        )

        sublime.message_dialog(
            message
        )


# ============================================================
# COMANDO 3
#
# CERRAR PESTAÑAS SIN GUARDAR VACÍAS
# ============================================================

class CloseEmptyUnsavedTabsCommand(
    sublime_plugin.WindowCommand
):

    def run(self):

        unsaved_views = get_unsaved_views(
            self.window
        )

        safe_empty_views = []

        skipped_dirty_empty_views = []

        # ----------------------------------------------------
        # Clasificar pestañas
        # ----------------------------------------------------

        for view in unsaved_views:

            size = view.size()

            is_dirty = view.is_dirty()

            if size == 0 and not is_dirty:

                safe_empty_views.append(
                    view
                )

            elif size == 0 and is_dirty:

                skipped_dirty_empty_views.append(
                    view
                )

        number_of_safe_views = len(
            safe_empty_views
        )

        number_of_skipped_views = len(
            skipped_dirty_empty_views
        )

        # ----------------------------------------------------
        # Nada para cerrar
        # ----------------------------------------------------

        if number_of_safe_views == 0:

            message = (
                "No hay pestañas vacías que puedan "
                "cerrarse automáticamente."
            )

            if number_of_skipped_views > 0:

                message = (
                    message
                    + "\n\n"
                    + "Hay {} pestaña(s) vacía(s) "
                    + "marcada(s) como modificada(s). "
                    + "Por seguridad no se tocarán."
                ).format(
                    number_of_skipped_views
                )

            sublime.message_dialog(
                message
            )

            return

        # ----------------------------------------------------
        # Confirmación
        # ----------------------------------------------------

        message = (
            "Se encontraron {} pestaña(s) sin guardar, "
            "vacía(s) y sin modificaciones.\n\n"
            "Estas pestañas tienen 0 caracteres y "
            "pueden cerrarse de forma segura."
        ).format(
            number_of_safe_views
        )

        if number_of_skipped_views > 0:

            message = (
                message
                + "\n\n"
                + "{} pestaña(s) vacía(s) modificada(s) "
                + "serán ignoradas por seguridad."
            ).format(
                number_of_skipped_views
            )

        confirm = sublime.ok_cancel_dialog(
            message,
            "Cerrar vacías"
        )

        if not confirm:
            return

        # ----------------------------------------------------
        # Cerrar
        # ----------------------------------------------------

        closed_count = 0

        for view in safe_empty_views:

            # Comprobar nuevamente.
            if view.size() != 0:
                continue

            if view.is_dirty():
                continue

            self.window.focus_view(
                view
            )

            self.window.run_command(
                "close"
            )

            closed_count = closed_count + 1

        result_message = (
            "Se cerraron {} pestaña(s) "
            "vacía(s)."
        ).format(
            closed_count
        )

        sublime.message_dialog(
            result_message
        )


# ============================================================
# COMANDO 4
#
# CERRAR TODAS LAS PESTAÑAS SIN GUARDAR
# ============================================================

class CloseAllUnsavedTabsCommand(
    sublime_plugin.WindowCommand
):

    def run(self):

        unsaved_views = get_unsaved_views(
            self.window
        )

        number_of_views = len(
            unsaved_views
        )

        if number_of_views == 0:

            sublime.message_dialog(
                "No hay pestañas sin guardar "
                "en esta ventana."
            )

            return

        # ----------------------------------------------------
        # Contar estados
        # ----------------------------------------------------

        empty_count = 0
        content_count = 0
        dirty_count = 0

        for view in unsaved_views:

            if view.size() == 0:
                empty_count = empty_count + 1

            else:
                content_count = content_count + 1

            if view.is_dirty():
                dirty_count = dirty_count + 1

        # ----------------------------------------------------
        # Advertencia
        # ----------------------------------------------------

        message = (
            "ATENCIÓN\n\n"
            "Se cerrarán TODAS las pestañas sin guardar "
            "de esta ventana.\n\n"
            "Total: {}\n"
            "Vacías: {}\n"
            "Con contenido: {}\n"
            "Marcadas como modificadas: {}\n\n"
            "El contenido de las pestañas sin guardar "
            "será DESCARTADO.\n\n"
            "Esta acción no se puede deshacer.\n\n"
            "Se recomienda ejecutar primero:\n"
            "\"Tab Admin: Respaldar pestañas sin guardar\""
        ).format(
            number_of_views,
            empty_count,
            content_count,
            dirty_count
        )

        confirm = sublime.ok_cancel_dialog(
            message,
            "Cerrar TODAS"
        )

        if not confirm:
            return

        # ----------------------------------------------------
        # Cerrar pestañas
        # ----------------------------------------------------

        closed_count = 0
        skipped_count = 0

        for view in unsaved_views:

            # Puede haber sido guardada entretanto.
            if view.file_name() is not None:

                skipped_count = skipped_count + 1

                continue

            # Evitar diálogo individual de guardado.
            view.set_scratch(
                True
            )

            self.window.focus_view(
                view
            )

            self.window.run_command(
                "close_file"
            )

            closed_count = closed_count + 1

        # ----------------------------------------------------
        # Resultado
        # ----------------------------------------------------

        result_message = (
            "Proceso terminado.\n\n"
            "Pestañas cerradas: {}"
        ).format(
            closed_count
        )

        if skipped_count > 0:

            result_message = (
                result_message
                + "\n\n"
                + "Pestañas ignoradas porque ya estaban "
                + "guardadas: {}"
            ).format(
                skipped_count
            )

        sublime.message_dialog(
            result_message
        )


# ============================================================
# SISTEMA AUTOMÁTICO DE ALERTAS
# ============================================================
#
# Los niveles se obtienen desde:
#
#     TabAdmin.sublime-settings
#
# Valores por defecto:
#
#     10  -> Aviso
#     25  -> Advertencia
#     50  -> Alerta importante
#     100 -> Respaldo muy recomendado
#
# Cada alerta ofrece:
#
#     Crear respaldo ahora
#     !!! CERRAR TODAS !!!
#     Cancelar
#
# ============================================================


class UnsavedTabLimitAlertListener(
    sublime_plugin.EventListener
):

    """
    Supervisa automáticamente la cantidad de pestañas
    sin guardar de cada ventana de Sublime Text.
    """

    # Nivel ya notificado por cada ventana.
    window_alert_levels = {}


    # ========================================================
    # EVENTO:
    # NUEVA PESTAÑA
    # ========================================================

    def on_new(
        self,
        view
    ):

        window = view.window()

        if window is None:
            return

        sublime.set_timeout(
            lambda: self.check_window(window),
            150
        )


    # ========================================================
    # EVENTO:
    # PESTAÑA GUARDADA
    # ========================================================

    def on_post_save(
        self,
        view
    ):

        window = view.window()

        if window is None:
            return

        sublime.set_timeout(
            lambda: self.check_window(window),
            150
        )


    # ========================================================
    # EVENTO:
    # PESTAÑA CERRADA
    # ========================================================

    def on_pre_close(
        self,
        view
    ):

        window = view.window()

        if window is None:
            return

        sublime.set_timeout(
            lambda: self.check_window(window),
            250
        )


    # ========================================================
    # CALCULAR NIVEL DE ALERTA
    # ========================================================

    def get_alert_level(
        self,
        unsaved_count
    ):

        """
        Determina el nivel según TabAdmin.sublime-settings.

        Devuelve:

            0 = sin alerta
            1 = aviso
            2 = advertencia
            3 = alerta importante
            4 = alerta crítica
        """

        info_level = get_setting_integer(
            "alert_level_info",
            10
        )

        warning_level = get_setting_integer(
            "alert_level_warning",
            25
        )

        important_level = get_setting_integer(
            "alert_level_important",
            50
        )

        critical_level = get_setting_integer(
            "alert_level_critical",
            100
        )

        if unsaved_count >= critical_level:
            return 4

        if unsaved_count >= important_level:
            return 3

        if unsaved_count >= warning_level:
            return 2

        if unsaved_count >= info_level:
            return 1

        return 0


    # ========================================================
    # COMPROBAR ESTADO DE LA VENTANA
    # ========================================================

    def check_window(
        self,
        window
    ):

        if window is None:
            return

        # ----------------------------------------------------
        # Alertas desactivadas
        # ----------------------------------------------------

        if not alerts_are_enabled():
            return

        # ----------------------------------------------------
        # Contar pestañas sin guardar
        # ----------------------------------------------------

        unsaved_views = get_unsaved_views(
            window
        )

        unsaved_count = len(
            unsaved_views
        )

        current_level = self.get_alert_level(
            unsaved_count
        )

        window_id = window.id()

        previous_level = self.window_alert_levels.get(
            window_id,
            0
        )

        # ----------------------------------------------------
        # Bajamos de nivel
        # ----------------------------------------------------

        if current_level < previous_level:

            self.window_alert_levels[
                window_id
            ] = current_level

            return

        # ----------------------------------------------------
        # Seguimos en el mismo nivel
        # ----------------------------------------------------

        if current_level == previous_level:
            return

        # ----------------------------------------------------
        # Subimos de nivel
        # ----------------------------------------------------

        self.window_alert_levels[
            window_id
        ] = current_level

        self.show_alert(
            window,
            unsaved_count,
            current_level
        )


    # ========================================================
    # DIÁLOGO CON TRES OPCIONES
    # ========================================================

    def offer_actions(
        self,
        window,
        message
    ):

        """
        Opciones:

        YES:
            Crear respaldo ahora

        NO:
            Cerrar todas las pestañas sin guardar

        CANCEL:
            No hacer nada
        """

        result = sublime.yes_no_cancel_dialog(
            message,
            "Crear respaldo ahora",
            "!!! CERRAR TODAS !!!"
        )

        # ----------------------------------------------------
        # CREAR RESPALDO
        # ----------------------------------------------------

        if result == sublime.DIALOG_YES:

            window.run_command(
                "backup_unsaved_tabs"
            )

            return

        # ----------------------------------------------------
        # CERRAR TODAS
        # ----------------------------------------------------

        if result == sublime.DIALOG_NO:

            window.run_command(
                "close_all_unsaved_tabs"
            )

            return

        # ----------------------------------------------------
        # CANCELAR
        # ----------------------------------------------------

        if result == sublime.DIALOG_CANCEL:
            return


    # ========================================================
    # MOSTRAR ALERTA SEGÚN EL NIVEL
    # ========================================================

    def show_alert(
        self,
        window,
        unsaved_count,
        alert_level
    ):

        """
        Muestra el mensaje correspondiente al nivel alcanzado.

        Los valores numéricos se leen dinámicamente desde
        TabAdmin.sublime-settings.
        """

        # ----------------------------------------------------
        # Leer límites configurados
        # ----------------------------------------------------

        info_level = get_setting_integer(
            "alert_level_info",
            10
        )

        warning_level = get_setting_integer(
            "alert_level_warning",
            25
        )

        important_level = get_setting_integer(
            "alert_level_important",
            50
        )

        critical_level = get_setting_integer(
            "alert_level_critical",
            100
        )


        # ====================================================
        # NIVEL 1
        #
        # AVISO
        # ====================================================

        if alert_level == 1:

            message = (
                "TAB ADMIN - AVISO\n\n"
                "Tienes {} pestañas sin guardar "
                "en esta ventana.\n\n"
                "Has alcanzado el nivel de {} pestañas "
                "sin guardar.\n\n"
                "Todavía es una cantidad manejable, "
                "pero puedes crear un respaldo preventivo "
                "o limpiar todas las pestañas temporales.\n\n"
                "Selecciona una acción."
            ).format(
                unsaved_count,
                info_level
            )

            self.offer_actions(
                window,
                message
            )

            return


        # ====================================================
        # NIVEL 2
        #
        # ADVERTENCIA
        # ====================================================

        if alert_level == 2:

            message = (
                "TAB ADMIN - ADVERTENCIA\n\n"
                "Tienes {} pestañas sin guardar "
                "en esta ventana.\n\n"
                "Has alcanzado o superado el nivel "
                "de {} pestañas sin guardar.\n\n"
                "La cantidad de contenido temporal "
                "está comenzando a crecer.\n\n"
                "Puedes crear un respaldo, cerrar todas "
                "las pestañas sin guardar o continuar "
                "trabajando sin realizar ninguna acción."
            ).format(
                unsaved_count,
                warning_level
            )

            self.offer_actions(
                window,
                message
            )

            return


        # ====================================================
        # NIVEL 3
        #
        # ALERTA IMPORTANTE
        # ====================================================

        if alert_level == 3:

            message = (
                "TAB ADMIN - ALERTA IMPORTANTE\n\n"
                "Tienes {} pestañas sin guardar "
                "en esta ventana.\n\n"
                "Has alcanzado o superado el nivel "
                "de {} pestañas sin guardar.\n\n"
                "Existe un volumen considerable de "
                "información temporal abierta.\n\n"
                "Se recomienda crear un respaldo antes "
                "de continuar acumulando pestañas.\n\n"
                "También puedes cerrar todas las pestañas "
                "sin guardar si ya no necesitas "
                "su contenido."
            ).format(
                unsaved_count,
                important_level
            )

            self.offer_actions(
                window,
                message
            )

            return


        # ====================================================
        # NIVEL 4
        #
        # RESPALDO MUY RECOMENDADO
        # ====================================================

        if alert_level == 4:

            message = (
                "TAB ADMIN - RESPALDO MUY RECOMENDADO\n\n"
                "Tienes {} pestañas sin guardar "
                "en esta ventana.\n\n"
                "Has alcanzado o superado el nivel "
                "de {} pestañas sin guardar.\n\n"
                "Existe una cantidad importante de "
                "información temporal abierta.\n\n"
                "Una interrupción inesperada de Sublime, "
                "Windows o del equipo podría poner "
                "este contenido en riesgo.\n\n"
                "RECOMENDACIÓN:\n\n"
                "Crea un respaldo antes de cerrar "
                "las pestañas sin guardar."
            ).format(
                unsaved_count,
                critical_level
            )

            self.offer_actions(
                window,
                message
            )

            return