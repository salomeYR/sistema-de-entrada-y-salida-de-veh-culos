Sistema de entrada y salida de vehículos - Autos Colombia

Sistema web para controlar un parqueadero por mensualidad. Reemplaza el control manual por uno digital: registra entradas y salidas, valida la mensualidad, administra las celdas y lleva el historial.

Proyecto académico de Tecnología de Diseño de Software (Ingeniería de Software, Medellín, 2026).

Estado del proyecto
Iteración	Alcance                                   	Estado
1	        Gestión de entrada y salida de vehículos	Terminada
2	        Gestión de usuarios, vehículos y celdas	    Terminada
3	        Gestión de pagos	                        Pendiente

Funcionalidades

Iteración 1: entrada y salida

Registrar la entrada de un vehículo con su celda; la fecha y la hora se guardan solas.
Validar que la placa exista, que la mensualidad esté vigente y que el vehículo no esté ya dentro.
Registrar la salida y liberar la celda.
Listar los vehículos que están dentro y mostrar el resumen en la pantalla de inicio.
Registrar novedades y consultar el historial filtrando por placa y fecha.

Iteración 2: usuarios, vehículos y celdas

Registrar, buscar, editar, desactivar y reactivar usuarios (el documento es único).
Registrar, editar y retirar vehículos asociados a un usuario. Formato de placa: carro ABC123, moto ABC12D.
Registrar, filtrar, editar, deshabilitar, habilitar y eliminar celdas, con resumen de ocupación por tipo.
Las bajas son lógicas: se conserva el historial de accesos.
Un usuario inactivo, un vehículo retirado o una celda deshabilitada no pueden usarse en una entrada.

Arquitectura

Arquitectura en capas: los controladores reciben las peticiones, los servicios aplican las reglas de negocio y los modelos acceden a los datos.