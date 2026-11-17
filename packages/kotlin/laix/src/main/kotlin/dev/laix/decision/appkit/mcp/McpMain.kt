package dev.laix.decision.appkit.mcp

import kotlin.system.exitProcess

/** Run the LAIX MCP server over stdio. */
fun main(args: Array<String>) {
    var transport = "stdio"
    var index = 0
    while (index < args.size) {
        if (args[index] == "--transport") {
            transport = args.getOrNull(index + 1) ?: "stdio"
            index += 2
        } else {
            index++
        }
    }
    if (transport != "stdio") {
        System.err.println("laix-mcp: unknown transport '$transport'")
        exitProcess(2)
    }
    McpStdioServer().run()
}
