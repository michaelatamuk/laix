plugins {
    kotlin("jvm") version "2.1.20"
    application
}

val laixVersion: String by project

group = "dev.laix"
version = laixVersion

kotlin {
    jvmToolchain(17)
}

dependencies {
    implementation("dev.laix:laix-decision:$laixVersion")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.1")
    testImplementation(kotlin("test-junit5"))
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

application {
    mainClass.set("dev.laix.examples.MainKt")
}

tasks.test {
    useJUnitPlatform()
}
