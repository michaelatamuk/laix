plugins {
    kotlin("jvm") version "2.1.20"
    application
}

group = "dev.laix"
version = "0.18.0"

kotlin {
    jvmToolchain(17)
}

application {
    mainClass.set("dev.laix.decision.appkit.cli.MainKt")
}

tasks.register<JavaExec>("bench") {
    group = "application"
    description = "Run the LAIX decision-class bench"
    mainClass.set("dev.laix.decision.evaluation.bench.BenchMainKt")
    classpath = sourceSets["main"].runtimeClasspath
}

tasks.register<JavaExec>("mcp") {
    group = "application"
    description = "Run the LAIX MCP server over stdio"
    mainClass.set("dev.laix.decision.appkit.mcp.McpMainKt")
    classpath = sourceSets["main"].runtimeClasspath
}

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.1")
    testImplementation(kotlin("test-junit5"))
    testImplementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.0")
    testImplementation("com.networknt:json-schema-validator:1.5.6")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
}
