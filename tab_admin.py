import sublime
import sublime_plugin
import os
import datetime


# ============================================================
# TAB ADMIN PARA SUBLIME TEXT 3
# ============================================================
#
# Este plugin administra las pestañas / buffers que todavía
# NO han sido guardados como archivos físicos.
#
# IMPORTANTE:
#
# No dependemos del texto "Untitled".
#
# Una pestaña sin guardar se identifica mediante:
#
#     view.file_name() is None
#
# Esto funciona incluso cuando Sublime cambia visualmente
# "Untitled" por la primera línea escrita dentro del documento.
#
# Funciones actuales:
#
# 1. Listar todas las pestañas sin guardar.
# 2. Mostrar una vista previa de su contenido.
# 3. Saltar directamente a una pestaña seleccionada.
# 4. Crear un respaldo de todas las pestañas sin guardar.
# 5. Cerrar solamente pestañas vacías y no modificadas.
#
# ============================================================


# ------------------------------------------------------------
# COMPROBAR SI UNA VISTA ES UN BUFFER SIN GUARDAR
# ------------------------------------------------------------

def is_unsaved_view(view):
    """
    Devuelve True si la pestaña todavía no tiene
    un archivo físico asociado en disco.
    """

    if view.file_name() is None:
        return True

    return False


# ------------------------------------------------------------
# OBTENER TODAS LAS PESTAÑAS SIN GUARDAR
# ------------------------------------------------------------

def get_unsaved_views(window):
    """
    Recorre todas las pestañas abiertas de la ventana actual
    y devuelve solamente aquellas que todavía no han sido
    guardadas como archivo.
    """

    unsaved_views = []

    all_views = window.views()

    for view in all_views:

        if is_unsaved_view(view):
            unsaved_views.append(view)

    return unsaved_views


# ------------------------------------------------------------
# OBTENER UN NOMBRE ÚTIL PARA MOSTRAR LA PESTAÑA
# ------------------------------------------------------------

def get_view_title(view):
    """
    Obtiene el nombre visible de una pestaña.

    Sublime puede utilizar la primera línea del contenido
    como título de una pestaña sin guardar.

    Si no existe ningún nombre, mostramos "Untitled".
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
    Indica si Sublime considera que la pestaña tiene
    cambios pendientes.
    """

    if view.is_dirty():
        return "MODIFICADA"

    return "sin cambios"


# ------------------------------------------------------------
# OBTENER VISTA PREVIA DEL CONTENIDO
# ------------------------------------------------------------

def get_preview_text(view, limit=180):
    """
    Devuelve los primeros caracteres del documento para
    mostrarlos en el panel de administración.

    Los saltos de línea se convierten en espacios para
    mantener la vista previa compacta.
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
# OBTENER TODO EL CONTENIDO DE UNA PESTAÑA
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
# BUSCAR DIRECTORIO PARA GUARDAR RESPALDOS
# ------------------------------------------------------------

def get_backup_directory():
    """
    Intenta utilizar el Escritorio del usuario.

    Primero prueba:

        ~/Desktop

    Luego:

        ~/Escritorio

    Si ninguno existe, utiliza:

        Packages/User/TabAdmin_Backups
    """

    home_directory = os.path.expanduser(
        "~"
    )

    # --------------------------------------------------------
    # Intentar Desktop
    # --------------------------------------------------------

    desktop_directory = os.path.join(
        home_directory,
        "Desktop"
    )

    if os.path.isdir(desktop_directory):
        return desktop_directory

    # --------------------------------------------------------
    # Intentar Escritorio
    # --------------------------------------------------------

    desktop_directory = os.path.join(
        home_directory,
        "Escritorio"
    )

    if os.path.isdir(desktop_directory):
        return desktop_directory

    # --------------------------------------------------------
    # Directorio alternativo dentro de Sublime
    # --------------------------------------------------------

    backup_directory = os.path.join(
        sublime.packages_path(),
        "User",
        "TabAdmin_Backups"
    )

    if not os.path.isdir(backup_directory):

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
        """
        Abre un Quick Panel mostrando solamente los
        documentos que todavía no han sido guardados.
        """

        self.unsaved_views = get_unsaved_views(
            self.window
        )

        number_of_views = len(
            self.unsaved_views
        )

        # ----------------------------------------------------
        # No encontramos documentos sin guardar.
        # ----------------------------------------------------

        if number_of_views == 0:

            sublime.message_dialog(
                "No hay pestañas sin guardar "
                "en esta ventana."
            )

            return

        # ----------------------------------------------------
        # Construir elementos del Quick Panel.
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Mostrar panel.
        # ----------------------------------------------------

        self.window.show_quick_panel(
            items,
            self.on_select
        )


    def on_select(self, index):
        """
        Sublime llama esta función cuando seleccionamos
        una pestaña del listado.
        """

        # -1 significa que el usuario canceló.
        if index == -1:
            return

        number_of_views = len(
            self.unsaved_views
        )

        # Protección adicional.
        if index >= number_of_views:
            return

        selected_view = self.unsaved_views[
            index
        ]

        # Llevar al usuario directamente a esa pestaña.
        self.window.focus_view(
            selected_view
        )


# ============================================================
# COMANDO 2
#
# CREAR RESPALDO DE TODAS LAS PESTAÑAS SIN GUARDAR
# ============================================================

class BackupUnsavedTabsCommand(
    sublime_plugin.WindowCommand
):

    def run(self):
        """
        Guarda en un archivo TXT el contenido completo de
        todas las pestañas que todavía no tienen archivo
        físico asociado.
        """

        unsaved_views = get_unsaved_views(
            self.window
        )

        number_of_views = len(
            unsaved_views
        )

        # ----------------------------------------------------
        # No tenemos nada que respaldar.
        # ----------------------------------------------------

        if number_of_views == 0:

            sublime.message_dialog(
                "No hay pestañas sin guardar "
                "para respaldar."
            )

            return

        # ----------------------------------------------------
        # Crear fecha/hora para identificar el respaldo.
        # ----------------------------------------------------

        current_time = datetime.datetime.now()

        timestamp = current_time.strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

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
        # Construir contenido del respaldo.
        # ----------------------------------------------------

        content = []

        content.append(
            "RESPALDO DE PESTAÑAS SIN GUARDAR"
        )

        content.append(
            "=" * 78
        )

        content.append(
            ""
        )

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

        content.append(
            ""
        )

        content.append(
            "=" * 78
        )

        content.append(
            ""
        )

        position = 1

        # ----------------------------------------------------
        # Agregar cada pestaña al respaldo.
        # ----------------------------------------------------

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

            content.append(
                ""
            )

            content.append(
                "CONTENIDO:"
            )

            content.append(
                "-" * 78
            )

            content.append(
                text
            )

            content.append(
                ""
            )

            content.append(
                ""
            )

            content.append(
                "=" * 78
            )

            content.append(
                ""
            )

            position = position + 1

        # ----------------------------------------------------
        # Convertir lista a texto.
        # ----------------------------------------------------

        final_content = "\n".join(
            content
        )

        # ----------------------------------------------------
        # Guardar el archivo.
        # ----------------------------------------------------

        try:

            backup_file = open(
                output_file,
                "w",
                encoding="utf-8"
            )

            backup_file.write(
                final_content
            )

            backup_file.close()

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
        # Confirmación.
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
# CERRAR PESTAÑAS SIN GUARDAR COMPLETAMENTE VACÍAS
# ============================================================

class CloseEmptyUnsavedTabsCommand(
    sublime_plugin.WindowCommand
):

    def run(self):
        """
        Busca documentos sin guardar completamente vacíos.

        Por seguridad, solamente cierra aquellos que:

        1. No tienen archivo asociado.
        2. Tienen 0 caracteres.
        3. Sublime NO los considera modificados.

        Si un documento está vacío pero aparece como modificado,
        NO se cerrará automáticamente.
        """

        unsaved_views = get_unsaved_views(
            self.window
        )

        safe_empty_views = []

        skipped_dirty_empty_views = []

        # ----------------------------------------------------
        # Clasificar documentos vacíos.
        # ----------------------------------------------------

        for view in unsaved_views:

            size = view.size()

            is_dirty = view.is_dirty()

            # ------------------------------------------------
            # Vacío y no modificado:
            # seguro para cerrar.
            # ------------------------------------------------

            if size == 0 and not is_dirty:

                safe_empty_views.append(
                    view
                )

            # ------------------------------------------------
            # Vacío pero Sublime dice que fue modificado:
            # no lo cerramos automáticamente.
            # ------------------------------------------------

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
        # Nada seguro para cerrar.
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
        # Confirmación antes de cerrar.
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
        # Cerrar.
        # ----------------------------------------------------

        closed_count = 0

        for view in safe_empty_views:

            # ------------------------------------------------
            # Comprobar nuevamente justo antes de cerrar.
            # ------------------------------------------------

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

        # ----------------------------------------------------
        # Resultado.
        # ----------------------------------------------------

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
        """
        Cierra TODAS las pestañas que todavía no tienen
        un archivo físico asociado.

        Esto incluye:

        - Pestañas vacías.
        - Pestañas con contenido.
        - Pestañas modificadas.
        - Pestañas cuyo título ya no dice "Untitled".

        IMPORTANTE:

        El contenido de estas pestañas será descartado.

        Para evitar que Sublime muestre un diálogo de
        guardado por cada pestaña, antes de cerrarla
        se convierte temporalmente en una vista scratch.
        """

        # ----------------------------------------------------
        # Obtener todas las pestañas sin guardar.
        # ----------------------------------------------------

        unsaved_views = get_unsaved_views(
            self.window
        )

        number_of_views = len(
            unsaved_views
        )

        # ----------------------------------------------------
        # No hay nada que cerrar.
        # ----------------------------------------------------

        if number_of_views == 0:

            sublime.message_dialog(
                "No hay pestañas sin guardar "
                "en esta ventana."
            )

            return

        # ----------------------------------------------------
        # Contar pestañas según su estado.
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
        # Mostrar advertencia antes de hacer nada.
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

        # ----------------------------------------------------
        # El usuario canceló.
        # ----------------------------------------------------

        if not confirm:
            return

        # ----------------------------------------------------
        # Cerrar pestañas.
        # ----------------------------------------------------

        closed_count = 0
        skipped_count = 0

        for view in unsaved_views:

            # ------------------------------------------------
            # Comprobar nuevamente justo antes de cerrarla.
            #
            # Es importante porque una pestaña podría haber
            # sido guardada mientras el comando estaba activo.
            # ------------------------------------------------

            if view.file_name() is not None:

                skipped_count = skipped_count + 1

                continue

            # ------------------------------------------------
            # Marcar como scratch.
            #
            # Esto permite descartarla sin que Sublime
            # pregunte si queremos guardar los cambios.
            # ------------------------------------------------

            view.set_scratch(
                True
            )

            # ------------------------------------------------
            # Dar foco a la pestaña que vamos a cerrar.
            # ------------------------------------------------

            self.window.focus_view(
                view
            )

            # ------------------------------------------------
            # Cerrar la pestaña enfocada.
            # ------------------------------------------------

            self.window.run_command(
                "close_file"
            )

            closed_count = closed_count + 1

        # ----------------------------------------------------
        # Mostrar resultado.
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
# PARA PESTAÑAS SIN GUARDAR
# ============================================================
#
# NIVELES:
#
#     10 pestañas  -> Aviso
#     25 pestañas  -> Advertencia
#     50 pestañas  -> Alerta importante
#     100 pestañas -> Respaldo muy recomendado
#
# En TODOS los niveles aparecen tres opciones:
#
#     [ Crear respaldo ahora ]
#     [ !!! CERRAR TODAS !!! ]
#     [ Cancelar ]
#
# IMPORTANTE:
#
# - "Crear respaldo ahora" ejecuta backup_unsaved_tabs.
# - "Cerrar todas" ejecuta close_all_unsaved_tabs.
# - "Cancelar" no hace nada.
#
# El botón de cierre NO puede pintarse de rojo mediante
# la API nativa de Sublime Text 3.
#
# ============================================================


# ------------------------------------------------------------
# CONFIGURACIÓN DE LOS NIVELES
# ------------------------------------------------------------

UNSAVED_LEVEL_INFO = 10
UNSAVED_LEVEL_WARNING = 25
UNSAVED_LEVEL_IMPORTANT = 50
UNSAVED_LEVEL_CRITICAL = 100


# ============================================================
# LISTENER PRINCIPAL
# ============================================================

class UnsavedTabLimitAlertListener(
    sublime_plugin.EventListener
):

    """
    Supervisa automáticamente la cantidad de pestañas
    sin guardar de cada ventana de Sublime Text.

    Cada ventana mantiene su propio nivel de alerta.
    """

    # --------------------------------------------------------
    # Guarda el último nivel alcanzado por cada ventana.
    #
    # Ejemplo:
    #
    # {
    #     1: 2,
    #     3: 4
    # }
    #
    # Ventana 1 -> nivel 25
    # Ventana 3 -> nivel 100
    # --------------------------------------------------------

    window_alert_levels = {}


    # ========================================================
    # EVENTO:
    # CREACIÓN DE UNA NUEVA PESTAÑA
    # ========================================================

    def on_new(self, view):

        window = view.window()

        if window is None:
            return

        sublime.set_timeout(
            lambda: self.check_window(window),
            150
        )


    # ========================================================
    # EVENTO:
    # UNA PESTAÑA ES GUARDADA
    # ========================================================

    def on_post_save(self, view):

        window = view.window()

        if window is None:
            return

        sublime.set_timeout(
            lambda: self.check_window(window),
            150
        )


    # ========================================================
    # EVENTO:
    # UNA PESTAÑA VA A CERRARSE
    # ========================================================

    def on_pre_close(self, view):

        window = view.window()

        if window is None:
            return

        sublime.set_timeout(
            lambda: self.check_window(window),
            250
        )


    # ========================================================
    # CALCULAR NIVEL ACTUAL
    # ========================================================

    def get_alert_level(
        self,
        unsaved_count
    ):

        """
        Devuelve:

            0 = menos de 10
            1 = 10 a 24
            2 = 25 a 49
            3 = 50 a 99
            4 = 100 o más
        """

        if unsaved_count >= UNSAVED_LEVEL_CRITICAL:
            return 4

        if unsaved_count >= UNSAVED_LEVEL_IMPORTANT:
            return 3

        if unsaved_count >= UNSAVED_LEVEL_WARNING:
            return 2

        if unsaved_count >= UNSAVED_LEVEL_INFO:
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
        # Obtener todas las pestañas sin guardar.
        # ----------------------------------------------------

        unsaved_views = get_unsaved_views(
            window
        )

        unsaved_count = len(
            unsaved_views
        )

        # ----------------------------------------------------
        # Determinar nivel actual.
        # ----------------------------------------------------

        current_level = self.get_alert_level(
            unsaved_count
        )

        window_id = window.id()

        # ----------------------------------------------------
        # Nivel previamente registrado.
        # ----------------------------------------------------

        previous_level = self.window_alert_levels.get(
            window_id,
            0
        )


        # ====================================================
        # SI BAJAMOS DE NIVEL
        # ====================================================

        if current_level < previous_level:

            self.window_alert_levels[
                window_id
            ] = current_level

            return


        # ====================================================
        # SI SEGUIMOS EN EL MISMO NIVEL
        # ====================================================

        if current_level == previous_level:
            return


        # ====================================================
        # SI SUBIMOS DE NIVEL
        # ====================================================

        self.window_alert_levels[
            window_id
        ] = current_level

        self.show_alert(
            window,
            unsaved_count,
            current_level
        )


    # ========================================================
    # MOSTRAR DIÁLOGO CON TRES OPCIONES
    # ========================================================

    def offer_actions(
        self,
        window,
        message
    ):

        """
        Presenta tres decisiones:

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


        # ====================================================
        # CREAR RESPALDO
        # ====================================================

        if result == sublime.DIALOG_YES:

            window.run_command(
                "backup_unsaved_tabs"
            )

            return


        # ====================================================
        # CERRAR TODAS LAS PESTAÑAS SIN GUARDAR
        # ====================================================

        if result == sublime.DIALOG_NO:

            # ------------------------------------------------
            # Ejecutamos el comando que ya desarrollaste.
            #
            # Ese comando debe mantener su propia advertencia
            # y confirmación antes de descartar contenido.
            # ------------------------------------------------

            window.run_command(
                "close_all_unsaved_tabs"
            )

            return


        # ====================================================
        # CANCELAR
        # ====================================================

        if result == sublime.DIALOG_CANCEL:
            return


    # ========================================================
    # MOSTRAR ALERTA SEGÚN NIVEL
    # ========================================================

    def show_alert(
        self,
        window,
        unsaved_count,
        alert_level
    ):

        """
        Muestra una alerta distinta para cada nivel.

        Todas ofrecen:

            Crear respaldo ahora
            Cerrar todas
            Cancelar
        """


        # ====================================================
        # NIVEL 1
        #
        # 10 PESTAÑAS
        # ====================================================

        if alert_level == 1:

            message = (
                "TAB ADMIN - AVISO\n\n"

                "Tienes {} pestañas sin guardar "
                "en esta ventana.\n\n"

                "Has alcanzado las 10 pestañas "
                "sin guardar.\n\n"

                "Todavía es una cantidad manejable, "
                "pero puedes crear un respaldo preventivo "
                "o limpiar todas las pestañas temporales.\n\n"

                "Selecciona una acción."
            ).format(
                unsaved_count
            )

            self.offer_actions(
                window,
                message
            )

            return


        # ====================================================
        # NIVEL 2
        #
        # 25 PESTAÑAS
        # ====================================================

        if alert_level == 2:

            message = (
                "TAB ADMIN - ADVERTENCIA\n\n"

                "Tienes {} pestañas sin guardar "
                "en esta ventana.\n\n"

                "Has alcanzado o superado "
                "las 25 pestañas sin guardar.\n\n"

                "La cantidad de contenido temporal "
                "está comenzando a crecer.\n\n"

                "Puedes crear un respaldo, cerrar todas "
                "las pestañas sin guardar o continuar "
                "trabajando sin realizar ninguna acción."
            ).format(
                unsaved_count
            )

            self.offer_actions(
                window,
                message
            )

            return


        # ====================================================
        # NIVEL 3
        #
        # 50 PESTAÑAS
        # ====================================================

        if alert_level == 3:

            message = (
                "TAB ADMIN - ALERTA IMPORTANTE\n\n"

                "Tienes {} pestañas sin guardar "
                "en esta ventana.\n\n"

                "Has alcanzado o superado "
                "las 50 pestañas sin guardar.\n\n"

                "Existe un volumen considerable de "
                "información temporal abierta.\n\n"

                "Se recomienda crear un respaldo antes "
                "de continuar acumulando pestañas.\n\n"

                "También puedes cerrar todas las pestañas "
                "sin guardar si ya no necesitas "
                "su contenido."
            ).format(
                unsaved_count
            )

            self.offer_actions(
                window,
                message
            )

            return


        # ====================================================
        # NIVEL 4
        #
        # 100 PESTAÑAS
        # ====================================================

        if alert_level == 4:

            message = (
                "TAB ADMIN - RESPALDO MUY RECOMENDADO\n\n"

                "Tienes {} pestañas sin guardar "
                "en esta ventana.\n\n"

                "Has alcanzado o superado "
                "las 100 pestañas sin guardar.\n\n"

                "Existe una cantidad importante de "
                "información temporal abierta.\n\n"

                "Una interrupción inesperada de Sublime, "
                "Windows o del equipo podría poner "
                "este contenido en riesgo.\n\n"

                "RECOMENDACIÓN:\n\n"

                "Crea un respaldo antes de cerrar "
                "las pestañas sin guardar."
            ).format(
                unsaved_count
            )

            self.offer_actions(
                window,
                message
            )

            return