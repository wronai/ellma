"""
ELLMa Groovy Script Generator

This module generates Groovy scripts, particularly for Jenkins pipelines,
build automation, and DevOps tasks using LLM with built-in templates.
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from ellma.utils.logger import get_logger

logger = get_logger(__name__)

class GroovyGenerator:
    """
    Groovy Script Generator

    Generates Groovy scripts and Jenkins pipelines using LLM with
    built-in templates and best practices.
    """

    def __init__(self, agent):
        """Initialize Groovy Generator"""
        self.agent = agent
        self.templates = self._load_templates()
        self.jenkins_templates = self._load_jenkins_templates()

    def generate(self, task_description: str, **kwargs) -> str:
        """
        Generate Groovy script for given task

        Args:
            task_description: Description of what the script should do
            **kwargs: Additional parameters

        Returns:
            Generated Groovy script
        """
        # Extract parameters
        script_type = kwargs.get('type', 'script')  # script, jenkins, gradle
        pipeline_type = kwargs.get('pipeline', 'declarative')  # declarative, scripted
        stages = kwargs.get('stages', ['build', 'test', 'deploy'])

        # Check if we have an LLM available
        if not self.agent.llm:
            return self._generate_fallback_script(task_description, **kwargs)

        # Create generation prompt
        prompt = self._create_generation_prompt(task_description, **kwargs)

        try:
            # Generate script using LLM
            generated_script = self.agent.generate(prompt, max_tokens=1200)

            # Post-process and enhance the script
            enhanced_script = self._enhance_script(generated_script, **kwargs)

            # Validate the script
            validation_result = self._validate_script(enhanced_script)

            if validation_result['valid']:
                return enhanced_script
            else:
                logger.warning(f"Generated script validation failed: {validation_result['errors']}")
                # Try to fix common issues
                fixed_script = self._fix_common_issues(enhanced_script)
                return fixed_script

        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return self._generate_fallback_script(task_description, **kwargs)

    def _create_generation_prompt(self, task_description: str, **kwargs) -> str:
        """Create prompt for LLM script generation"""

        script_type = kwargs.get('type', 'script')
        pipeline_type = kwargs.get('pipeline', 'declarative')

        prompt = f"""Generate a Groovy script for the following task:
{task_description}

Script type: {script_type}
"""

        if script_type == 'jenkins':
            prompt += f"""
Pipeline type: {pipeline_type}

Requirements for Jenkins pipeline:
- Use {pipeline_type} pipeline syntax
- Include proper error handling and cleanup
- Use parallel stages where appropriate
- Include post-build actions
- Add proper logging and notifications
- Use environment variables for configuration
- Include security best practices
- Add timeout configurations
"""

            if pipeline_type == 'declarative':
                prompt += """
Example declarative pipeline structure:
```groovy
pipeline {
    agent any
    
    environment {
        // Environment variables
    }
    
    stages {
        stage('Build') {
            steps {
                // Build steps
            }
        }
        
        stage('Test') {
            steps {
                // Test steps
            }
        }
        
        stage('Deploy') {
            steps {
                // Deploy steps
            }
        }
    }
    
    post {
        always {
            // Cleanup
        }
        success {
            // Success actions
        }
        failure {
            // Failure actions
        }
    }
}
```
"""
        else:
            prompt += """
Requirements for Groovy script:
- Use proper Groovy syntax and idioms
- Include error handling with try-catch blocks
- Add logging for important operations
- Use meaningful variable names
- Include input validation where appropriate
- Follow Groovy best practices
"""

        prompt += "\nGenerate ONLY the Groovy script code, no explanations:"

        return prompt

    def _enhance_script(self, script: str, **kwargs) -> str:
        """Enhance generated script with additional features"""

        # Extract just the script code if wrapped in markdown
        script = self._extract_script_code(script)

        # Add header comment
        header = self._generate_header(**kwargs)
        script = header + '\n\n' + script

        script_type = kwargs.get('type', 'script')

        if script_type == 'jenkins':
            script = self._enhance_jenkins_pipeline(script, **kwargs)
        else:
            script = self._enhance_groovy_script(script, **kwargs)

        return script

    def _generate_header(self, **kwargs) -> str:
        """Generate script header"""
        task_description = kwargs.get('task_description', 'Generated script')

        return f'''/*
 * {task_description}
 * 
 * Generated by ELLMa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 * Type: {kwargs.get('type', 'script')}
 */'''

    def _extract_script_code(self, text: str) -> str:
        """Extract Groovy script from markdown blocks"""
        # Look for code blocks
        groovy_pattern = r'```(?:groovy|jenkins)?\n(.*?)\n```'
        match = re.search(groovy_pattern, text, re.DOTALL)

        if match:
            return match.group(1).strip()

        return text.strip()

    def _enhance_jenkins_pipeline(self, script: str, **kwargs) -> str:
        """Enhance Jenkins pipeline with additional features"""

        # Check if it's a declarative pipeline
        if 'pipeline {' in script:
            script = self._enhance_declarative_pipeline(script, **kwargs)
        else:
            script = self._enhance_scripted_pipeline(script, **kwargs)

        return script

    def _enhance_declarative_pipeline(self, script: str, **kwargs) -> str:
        """Enhance declarative Jenkins pipeline"""

        lines = script.split('\n')
        enhanced_lines = []

        for line in lines:
            enhanced_lines.append(line)

            # Add timeout after pipeline declaration
            if 'pipeline {' in line:
                enhanced_lines.append('    options {')
                enhanced_lines.append('        timeout(time: 1, unit: \'HOURS\')')
                enhanced_lines.append('        buildDiscarder(logRotator(numToKeepStr: \'10\'))')
                enhanced_lines.append('        skipDefaultCheckout()')
                enhanced_lines.append('    }')
                enhanced_lines.append('')

        # Add notifications if not present
        if 'post {' not in script:
            enhanced_lines.extend([
                '',
                '    post {',
                '        always {',
                '            cleanWs()',
                '        }',
                '        success {',
                '            echo "Pipeline completed successfully"',
                '        }',
                '        failure {',
                '            echo "Pipeline failed"',
                '            // Add notification logic here',
                '        }',
                '    }'
            ])

        return '\n'.join(enhanced_lines)

    def _enhance_scripted_pipeline(self, script: str, **kwargs) -> str:
        """Enhance scripted Jenkins pipeline"""

        if 'node' not in script:
            script = f'''node {{
    try {{
{self._indent_script(script, 2)}
    }} catch (Exception e) {{
        currentBuild.result = 'FAILURE'
        throw e
    }} finally {{
        cleanWs()
    }}
}}'''

        return script

    def _enhance_groovy_script(self, script: str, **kwargs) -> str:
        """Enhance regular Groovy script"""

        # Add imports if missing
        common_imports = [
            'import groovy.transform.Field',
            'import java.text.SimpleDateFormat',
            'import java.util.Date'
        ]

        if not any('import' in line for line in script.split('\n')[:10]):
            script = '\n'.join(common_imports) + '\n\n' + script

        # Wrap in main execution block if it's a standalone script
        if 'def main(' not in script and 'class ' not in script:
            script = f'''def main() {{
{self._indent_script(script, 1)}
}}

// Execute main function
main()'''

        return script

    def _indent_script(self, script: str, levels: int) -> str:
        """Indent script by specified levels"""
        indent = '    ' * levels
        return '\n'.join(indent + line if line.strip() else line for line in script.split('\n'))

    def _validate_script(self, script: str) -> Dict[str, Any]:
        """Validate Groovy script syntax and structure"""
        errors = []
        warnings = []

        # Basic syntax checks
        open_braces = script.count('{')
        close_braces = script.count('}')
        if open_braces != close_braces:
            errors.append(f"Mismatched braces: {open_braces} open, {close_braces} close")

        open_parens = script.count('(')
        close_parens = script.count(')')
        if open_parens != close_parens:
            errors.append(f"Mismatched parentheses: {open_parens} open, {close_parens} close")

        # Jenkins pipeline specific checks
        if 'pipeline {' in script:
            if 'stages {' not in script:
                warnings.append("Declarative pipeline missing 'stages' block")

            if 'agent' not in script:
                warnings.append("Pipeline missing 'agent' declaration")

        # Groovy specific checks
        lines = script.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('/*'):
                continue

            # Check for common syntax issues
            if line.endswith(',') and not any(keyword in line for keyword in ['def', 'class', 'if', 'for', 'while']):
                warnings.append(f"Line {i}: Unexpected trailing comma")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _fix_common_issues(self, script: str) -> str:
        """Fix common Groovy script issues"""
        lines = script.split('\n')
        fixed_lines = []

        for line in lines:
            # Fix common syntax issues
            # Remove trailing commas in inappropriate places
            if line.strip().endswith(',') and '{' not in line and '}' not in line:
                line = line.rstrip(',')

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def _generate_fallback_script(self, task_description: str, **kwargs) -> str:
        """Generate fallback script when LLM is not available"""

        script_type = kwargs.get('type', 'script')

        if script_type == 'jenkins':
            return self._generate_jenkins_template(task_description, **kwargs)
        elif script_type == 'gradle':
            return self._generate_gradle_template(task_description, **kwargs)
        else:
            return self._generate_groovy_template(task_description, **kwargs)

    def _generate_jenkins_template(self, task_description: str, **kwargs) -> str:
        """Generate Jenkins pipeline template"""

        pipeline_type = kwargs.get('pipeline', 'declarative')
        stages = kwargs.get('stages', ['build', 'test', 'deploy'])

        if pipeline_type == 'declarative':
            return f'''/*
 * {task_description}
 * Generated by ELLMa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 */

pipeline {{
    agent any
    
    options {{
        timeout(time: 1, unit: 'HOURS')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        skipDefaultCheckout()
    }}
    
    environment {{
        // Define environment variables here
        BUILD_NUMBER = "${{env.BUILD_NUMBER}}"
        WORKSPACE = "${{env.WORKSPACE}}"
    }}
    
    stages {{
{self._generate_pipeline_stages(stages)}
    }}
    
    post {{
        always {{
            echo 'Pipeline completed'
            cleanWs()
        }}
        success {{
            echo 'Pipeline succeeded'
            // Add success notifications here
        }}
        failure {{
            echo 'Pipeline failed'
            // Add failure notifications here
        }}
        unstable {{
            echo 'Pipeline is unstable'
        }}
    }}
}}'''

        else:  # scripted pipeline
            return f'''/*
 * {task_description}
 * Generated by ELLMa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 */

node {{
    try {{
        stage('Checkout') {{
            checkout scm
        }}
        
{self._generate_scripted_stages(stages)}
        
    }} catch (Exception e) {{
        currentBuild.result = 'FAILURE'
        echo "Pipeline failed: ${{e.getMessage()}}"
        throw e
    }} finally {{
        cleanWs()
    }}
}}'''

    def _generate_pipeline_stages(self, stages: List[str]) -> str:
        """Generate stages for declarative pipeline"""

        stage_templates = {
            'checkout': '''        stage('Checkout') {
            steps {
                checkout scm
                echo 'Source code checked out'
            }
        }''',

            'build': '''        stage('Build') {
            steps {
                echo 'Building application...'
                // Add build commands here
                // sh 'make build' or sh './gradlew build'
            }
        }''',

            'test': '''        stage('Test') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        echo 'Running unit tests...'
                        // sh './gradlew test'
                    }
                    post {
                        always {
                            // publishTestResults testResultsPattern: 'build/test-results/test/*.xml'
                        }
                    }
                }
                stage('Integration Tests') {
                    steps {
                        echo 'Running integration tests...'
                        // sh './gradlew integrationTest'
                    }
                }
            }
        }''',

            'quality': '''        stage('Code Quality') {
            steps {
                echo 'Running code quality checks...'
                // sh './gradlew sonarqube'
            }
        }''',

            'package': '''        stage('Package') {
            steps {
                echo 'Packaging application...'
                // sh './gradlew assemble'
                // archiveArtifacts artifacts: 'build/libs/*.jar'
            }
        }''',

            'deploy': '''        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying application...'
                // Add deployment commands here
            }
        }'''
        }

        # Always include checkout first
        result_stages = [stage_templates['checkout']]

        for stage in stages:
            if stage in stage_templates and stage != 'checkout':
                result_stages.append(stage_templates[stage])

        return '\n\n'.join(result_stages)

    def _generate_scripted_stages(self, stages: List[str]) -> str:
        """Generate stages for scripted pipeline"""

        stage_templates = {
            'build': '''        stage('Build') {
            echo 'Building application...'
            // Add build commands here
        }''',

            'test': '''        stage('Test') {
            echo 'Running tests...'
            // Add test commands here
        }''',

            'deploy': '''        stage('Deploy') {
            echo 'Deploying application...'
            // Add deployment commands here
        }'''
        }

        result_stages = []
        for stage in stages:
            if stage in stage_templates:
                result_stages.append(stage_templates[stage])

        return '\n\n'.join(result_stages)

    def _generate_gradle_template(self, task_description: str, **kwargs) -> str:
        """Generate Gradle build script template"""

        return f'''/*
 * {task_description}
 * Generated by ELLMa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 */

plugins {{
    id 'java'
    id 'application'
}}

group = 'com.example'
version = '1.0.0'

java {{
    sourceCompatibility = JavaVersion.VERSION_11
    targetCompatibility = JavaVersion.VERSION_11
}}

repositories {{
    mavenCentral()
}}

dependencies {{
    implementation 'org.springframework.boot:spring-boot-starter:2.7.0'
    testImplementation 'junit:junit:4.13.2'
    testImplementation 'org.springframework.boot:spring-boot-starter-test:2.7.0'
}}

application {{
    mainClass = 'com.example.Application'
}}

tasks.withType(Test) {{
    useJUnitPlatform()
}}

task customTask {{
    doLast {{
        println 'Custom task for: {task_description}'
        // Add custom task logic here
    }}
}}'''

    def _generate_groovy_template(self, task_description: str, **kwargs) -> str:
        """Generate general Groovy script template"""

        return f'''/*
 * {task_description}
 * Generated by ELLMa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 */

import groovy.transform.Field
import java.text.SimpleDateFormat
import java.util.Date

@Field def LOG_FORMAT = new SimpleDateFormat('yyyy-MM-dd HH:mm:ss')

def log(message) {{
    println "${{LOG_FORMAT.format(new Date())}} - $message"
}}

def main() {{
    log "Starting: {task_description}"
    
    try {{
        // TODO: Implement task logic here
        log "Task: {task_description}"
        log "Please implement the specific logic for this task."
        
        log "Task completed successfully"
        
    }} catch (Exception e) {{
        log "Error: ${{e.getMessage()}}"
        e.printStackTrace()
        System.exit(1)
    }}
}}

// Execute main function
main()'''

    def _load_templates(self) -> Dict[str, str]:
        """Load Groovy script templates"""

        return {
            'file_processing': '''
import java.nio.file.*

def processFiles(String directory) {
    def path = Paths.get(directory)
    
    Files.walk(path)
        .filter { Files.isRegularFile(it) }
        .forEach { file ->
            println "Processing: ${file.fileName}"
            // Add file processing logic here
        }
}

processFiles(".")
''',

            'http_client': '''
@Grab('org.apache.httpcomponents:httpclient:4.5.13')
import org.apache.http.client.methods.HttpGet
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

def httpClient = HttpClients.createDefault()

def get(String url) {
    def request = new HttpGet(url)
    def response = httpClient.execute(request)
    
    try {
        def entity = response.getEntity()
        return EntityUtils.toString(entity)
    } finally {
        response.close()
    }
}

// Example usage
def result = get("https://api.github.com/users/octocat")
println result
''',

            'json_processing': '''
@Grab('com.fasterxml.jackson.core:jackson-databind:2.14.0')
import com.fasterxml.jackson.databind.ObjectMapper

def mapper = new ObjectMapper()

def parseJson(String jsonString) {
    return mapper.readValue(jsonString, Map.class)
}

def toJson(Object obj) {
    return mapper.writeValueAsString(obj)
}

// Example usage
def data = [name: "John", age: 30]
def json = toJson(data)
println json

def parsed = parseJson(json)
println "Name: ${parsed.name}"
'''
        }

    def _load_jenkins_templates(self) -> Dict[str, str]:
        """Load Jenkins-specific templates"""

        return {
            'maven_build': '''
pipeline {
    agent any
    
    tools {
        maven 'Maven-3.8.1'
        jdk 'JDK-11'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                sh 'mvn clean compile'
            }
        }
        
        stage('Test') {
            steps {
                sh 'mvn test'
            }
            post {
                always {
                    publishTestResults testResultsPattern: 'target/surefire-reports/*.xml'
                }
            }
        }
        
        stage('Package') {
            steps {
                sh 'mvn package'
                archiveArtifacts artifacts: 'target/*.jar'
            }
        }
    }
}
''',

            'docker_build': '''
pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = "${env.JOB_NAME}:${env.BUILD_NUMBER}"
        DOCKER_REGISTRY = 'your-registry.com'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    def image = docker.build("${DOCKER_IMAGE}")
                }
            }
        }
        
        stage('Test') {
            steps {
                sh 'docker run --rm ${DOCKER_IMAGE} npm test'
            }
        }
        
        stage('Push to Registry') {
            when {
                branch 'main'
            }
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-registry-credentials') {
                        def image = docker.image("${DOCKER_IMAGE}")
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
    }
}
'''
        }

if __name__ == "__main__":
    # Test the generator
    class MockAgent:
        def __init__(self):
            self.llm = None

        def generate(self, prompt, **kwargs):
            return '''pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Building...'
            }
        }
    }
}'''

    agent = MockAgent()
    generator = GroovyGenerator(agent)

    # Test Jenkins pipeline generation
    pipeline = generator.generate("CI/CD pipeline for Java application", type="jenkins")
    print("Generated Jenkins pipeline:")
    print(pipeline)

    # Test Groovy script generation
    script = generator.generate("File processing script", type="script")
    print("\nGenerated Groovy script:")
    print(script[:300] + "...")